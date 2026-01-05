from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import datetime

class BillingManager:
    def __init__(self, config_manager, activity_logger=None):
        self.config = config_manager
        self.activity_logger = activity_logger

    def calculate_tax(self, price, tax_rate_percent, is_interstate=False, is_inclusive=False):
        """
        Returns dict with tax breakdown.
        """
        if is_inclusive:
            # Price = Taxable + Tax
            # Taxable = Price / (1 + rate/100)
            total_amount = price
            taxable_value = price / (1 + (tax_rate_percent / 100.0))
            tax_amt = total_amount - taxable_value
        else:
            # Exclusive: Price = Taxable
            taxable_value = price
            tax_amt = taxable_value * (tax_rate_percent / 100.0)
            total_amount = taxable_value + tax_amt
        
        breakdown = {
            "taxable_value": taxable_value,
            "total_tax": tax_amt,
            "total_amount": total_amount,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 0.0
        }
        
        if is_interstate:
            breakdown['igst'] = tax_amt
        else:
            breakdown['cgst'] = tax_amt / 2.0
            breakdown['sgst'] = tax_amt / 2.0
            
        return breakdown

    def generate_invoice(self, items, buyer_details, invoice_number, filename, discount=None):
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        elements = []
        styles = getSampleStyleSheet()
        
        # --- Modern Palette & Styles ---
        ACCENT_COLOR = colors.HexColor("#2c3e50") # Dark Blue-Grey
        LIGHT_BG = colors.HexColor("#f8f9fa")     # Very Light Grey
        TEXT_COLOR = colors.HexColor("#2c3e50")
        
        # Custom Styles
        style_title = styles['Heading1']
        style_title.fontName = 'Helvetica-Bold'
        style_title.fontSize = 18 # Reduced from 24
        style_title.textColor = ACCENT_COLOR
        style_title.alignment = 2 # Right
        
        style_store = styles['Normal']
        style_store.fontName = 'Helvetica-Bold'
        style_store.fontSize = 14
        style_store.textColor = colors.black
        
        style_body = styles['Normal']
        style_body.fontName = 'Helvetica'
        style_body.fontSize = 9
        style_body.leading = 12
        
        # --- 1. Header Section ---
        store_name = self.config.get('store_name', 'My Store')
        store_addr = self.config.get('store_address', 'Address Line 1\nCity, State - Zip')
        store_gstin = self.config.get('store_gstin', '')
        store_contact = self.config.get('store_contact', '')
        
        # Left: Store Info
        store_info = f"{store_addr}<br/>GSTIN: {store_gstin}<br/>Phone: {store_contact}"
        p_store_name = Paragraph(store_name, style_store)
        p_store_info = Paragraph(store_info, style_body)
        
        # Right: Invoice Title & Details
        inv_date = buyer_details.get('date', datetime.date.today())
        p_inv_title = Paragraph("TAX INVOICE", style_title)
        inv_details = f"<b>INVOICE NO:</b> {invoice_number}<br/><b>DATE:</b> {inv_date}"
        p_inv_details = Paragraph(inv_details, style_body)
        
        # Header Table
        header_data = [
            [p_store_name, p_inv_title],
            [p_store_info, p_inv_details]
        ]
        
        t_header = Table(header_data, colWidths=[100*mm, 90*mm])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,1), 'RIGHT'),
            ('BOTTOMPADDING', (0,1), (-1,1), 15),
            ('LINEBELOW', (0,1), (-1,1), 1, colors.lightgrey), # Separator line
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 15))

        # --- 2. Bill To Section ---
        buyer_name = buyer_details.get('name', 'N/A')
        buyer_contact = buyer_details.get('contact', '')
        
        # Grey Box for Customer
        cust_data = [[Paragraph(f"<b>BILL TO:</b><br/>{buyer_name}<br/>Phone: {buyer_contact}", style_body)]]
        t_cust = Table(cust_data, colWidths=[190*mm])
        t_cust.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
            ('BOX', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('topPadding', (0,0), (-1,-1), 8),
            ('bottomPadding', (0,0), (-1,-1), 8),
            ('leftPadding', (0,0), (-1,-1), 10),
        ]))
        elements.append(t_cust)
        elements.append(Spacer(1, 15))

        # --- 3. Items Table ---
        # Columns: SN, Description, Taxable, Tax, Total
        headers = ['SN', 'Description', 'Taxable', 'Tax (GST)', 'Amount']
        
        data = [headers]
        grand_total = 0.0
        
        is_interstate = buyer_details.get('is_interstate', False)
        is_inclusive = buyer_details.get('is_tax_inclusive', False)
        default_tax = self.config.get('gst_default_percent', 18.0)
        
        for idx, item in enumerate(items):
            price = float(item.get('price', 0))
            tax_calc = self.calculate_tax(price, default_tax, is_interstate, is_inclusive)
            
            # Format Taxes
            if is_interstate:
                tax_str = f"IGST {default_tax}%: {tax_calc['igst']:.2f}"
            else:
                tax_str = f"CGST: {tax_calc['cgst']:.2f}\nSGST: {tax_calc['sgst']:.2f}"
            
            # Extract IMEI with logic (clean raw string)
            raw_imei = str(item.get('unique_id', ''))
            # If 'imei' key exists, prefer it, else fallback to unique_id
            real_imei = str(item.get('imei', '')) or raw_imei
            
            row = [
                str(idx + 1),
                Paragraph(f"<b>{item.get('model', 'Unknown Model')}</b><br/>IMEI: {real_imei}", style_body),
                f"Rs. {tax_calc['taxable_value']:.2f}", # Fixed: Rs instead of Rupee Symbol
                Paragraph(tax_str, style_body),
                f"Rs. {tax_calc['total_amount']:.2f}"
            ]
            data.append(row)
            grand_total += tax_calc['total_amount']
            
        # Table Styling
        col_widths = [12*mm, 85*mm, 28*mm, 35*mm, 30*mm]
        t_items = Table(data, colWidths=col_widths, repeatRows=1)
        
        style_table = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            # Data Rows
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'), # Right align numbers
            ('ALIGN', (0, 1), (0, -1), 'CENTER'), # Center SN
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ])
        t_items.setStyle(style_table)
        elements.append(t_items)
        
        # --- 4. Summary & Totals ---
        # Right aligned summary table
        final_total = grand_total
        discount_rows = []
        
        if discount and discount.get('amount', 0) > 0:
            d_amt = float(discount['amount'])
            d_reason = discount.get('reason', 'Discount')
            discount_rows = [[f"Less: {d_reason}", f"- Rs. {d_amt:.2f}"]]
            final_total -= d_amt
            
        summary_data = [
            ['Sub Total:', f"Rs. {grand_total:.2f}"],
        ] + discount_rows + [
            ['Grand Total:', f"Rs. {final_total:.2f}"]
        ]
        
        t_summary = Table(summary_data, colWidths=[40*mm, 35*mm])
        t_summary.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Bold Grand Total
            ('FONTSIZE', (0,-1), (-1,-1), 12),
            ('TEXTCOLOR', (0,-1), (-1,-1), ACCENT_COLOR),
            ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        
        # Layout Summary to the Right
        summary_container = Table([[ '', t_summary]], colWidths=[115*mm, 75*mm])
        elements.append(summary_container)
        elements.append(Spacer(1, 30))
        
        # --- 5. Footer ---
        terms = self.config.get('invoice_terms', 'Goods once sold will not be taken back.')
        
        footer_left = Paragraph(f"<b>Terms & Conditions:</b><br/>{terms}", style_body)
        footer_right = Paragraph(f"<br/><br/>_______________________<br/><b>Authorized Signatory</b><br/>For {store_name}", style_body)
        
        t_footer = Table([[footer_left, footer_right]], colWidths=[120*mm, 70*mm])
        t_footer.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
        ]))
        elements.append(t_footer)
        
        # Bottom "Thank You"
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Thank you for your business!", styles['Heading4'])) # Centered by default style? No.
        
        doc.build(elements)
        
        if self.activity_logger:
            self.activity_logger.log("INVOICE_GEN", f"Invoice {invoice_number} generated for Rs. {final_total:.2f}")
            
        return True
