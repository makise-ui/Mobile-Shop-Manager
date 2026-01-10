from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import datetime
import hashlib

class BillingManager:
    def __init__(self, config_manager, activity_logger=None):
        self.config = config_manager
        self.activity_logger = activity_logger

    def calculate_tax(self, price, tax_rate_percent, is_interstate=False, is_inclusive=False):
        """
        Returns dict with tax breakdown.
        """
        if is_inclusive:
            total_amount = price
            taxable_value = price / (1 + (tax_rate_percent / 100.0))
            tax_amt = total_amount - taxable_value
        else:
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
        
        # --- Modern Palette ---
        ACCENT_COLOR = colors.HexColor("#2c3e50")
        LIGHT_BG = colors.HexColor("#f8f9fa")
        
        # --- Fixed Styles (Creating new objects to avoid contamination) ---
        
        # Store Name (Big, Center)
        style_store_header = ParagraphStyle(
            'StoreHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=24,
            textColor=ACCENT_COLOR,
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        # Standard Body (Left)
        style_body = ParagraphStyle(
            'BodyLeft',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            alignment=TA_LEFT
        )
        
        # Right Aligned Body (For Invoice Details)
        style_right = ParagraphStyle(
            'BodyRight',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            alignment=TA_RIGHT
        )
        
        # --- 1. Header Section ---
        store_name = self.config.get('store_name', 'My Store')
        store_addr = self.config.get('store_address', 'Address Line 1\nCity, State - Zip')
        store_gstin = self.config.get('store_gstin', '')
        store_contact = self.config.get('store_contact', '')
        
        # 1. Store Name
        elements.append(Paragraph(store_name, style_store_header))
        
        # 2. Details Row
        store_info = f"{store_addr}<br/>GSTIN: {store_gstin}<br/>Phone: {store_contact}"
        p_store_info = Paragraph(store_info, style_body)
        
        inv_date = buyer_details.get('date', datetime.date.today())
        inv_text = f"""<font size=12 color={ACCENT_COLOR}><b>TAX INVOICE</b></font><br/>
        <b>INVOICE NO:</b> {invoice_number}<br/>
        <b>DATE:</b> {inv_date}"""
        p_inv_details = Paragraph(inv_text, style_right)
        
        t_header = Table([[p_store_info, p_inv_details]], colWidths=[95*mm, 95*mm])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEBELOW', (0,0), (-1,-1), 1, colors.lightgrey),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 15))

        # --- 2. Bill To Section ---
        buyer_name = buyer_details.get('name', 'N/A')
        buyer_contact = buyer_details.get('contact', '')
        
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
        headers = ['SN', 'Description', 'Taxable', 'CGST', 'SGST', 'IGST', 'Amount']
        data = [headers]
        grand_total = 0.0
        
        is_interstate = buyer_details.get('is_interstate', False)
        is_inclusive = buyer_details.get('is_tax_inclusive', False)
        default_tax = self.config.get('gst_default_percent', 18.0)
        
        for idx, item in enumerate(items):
            price = float(item.get('price', 0))
            tax_calc = self.calculate_tax(price, default_tax, is_interstate, is_inclusive)
            
            raw_imei = str(item.get('unique_id', ''))
            real_imei = str(item.get('imei', '')) or raw_imei
            
            row = [
                str(idx + 1),
                Paragraph(f"<b>{item.get('model', 'Unknown Model')}</b><br/>IMEI: {real_imei}", style_body),
                f"{tax_calc['taxable_value']:.2f}",
                f"{tax_calc['cgst']:.2f}",
                f"{tax_calc['sgst']:.2f}",
                f"{tax_calc['igst']:.2f}",
                f"{tax_calc['total_amount']:.2f}"
            ]
            data.append(row)
            grand_total += tax_calc['total_amount']
            
        col_widths = [10*mm, 65*mm, 25*mm, 20*mm, 20*mm, 20*mm, 30*mm]
        t_items = Table(data, colWidths=col_widths, repeatRows=1)
        
        style_table = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ])
        t_items.setStyle(style_table)
        elements.append(t_items)
        
        # --- 4. Summary & Totals ---
        final_total = grand_total
        discount_rows = []
        if discount and discount.get('amount', 0) > 0:
            d_amt = float(discount['amount'])
            d_reason = discount.get('reason', 'Discount')
            discount_rows = [[f"Less: {d_reason}", f"- Rs. {d_amt:.2f}"]]
            final_total -= d_amt
            
        summary_data = [['Sub Total:', f"Rs. {grand_total:.2f}"]] + discount_rows + [['Grand Total:', f"Rs. {final_total:.2f}"]]
        t_summary = Table(summary_data, colWidths=[40*mm, 35*mm])
        t_summary.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,-1), (-1,-1), 12),
            ('TEXTCOLOR', (0,-1), (-1,-1), ACCENT_COLOR),
            ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        
        elements.append(Table([[ '', t_summary]], colWidths=[115*mm, 75*mm]))
        elements.append(Spacer(1, 30))
        
        # --- 5. Footer & Signature ---
        terms = self.config.get('invoice_terms', 'Goods once sold will not be taken back.')
        
        # Use formatted total for consistency
        verify_str = f"{invoice_number}|{buyer_name}|{final_total:.2f}|{store_name}"
        verify_hash = hashlib.sha256(verify_str.encode()).hexdigest()[:16].upper()
        formatted_hash = " ".join([verify_hash[i:i+4] for i in range(0, len(verify_hash), 4)])
        
        footer_left = Paragraph(f"<b>Terms & Conditions:</b><br/>{terms}", style_body)
        
        sign_text = f"""<br/><br/>_______________________<br/>
        <b>Authorized Signatory</b><br/>
        For {store_name}<br/><br/>
        <font size=7 name="Courier">Digital Verify: {formatted_hash}</font>
        """
        footer_right = Paragraph(sign_text, style_right)
        
        t_footer = Table([[footer_left, footer_right]], colWidths=[120*mm, 70*mm])
        t_footer.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
        ]))
        elements.append(t_footer)
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Thank you for your business!", styles['Heading4']))
        
        doc.build(elements)
        if self.activity_logger:
            self.activity_logger.log("INVOICE_GEN", f"Invoice {invoice_number} generated for Rs. {final_total:.2f}")
            
        return True, verify_hash, final_total
