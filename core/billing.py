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
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()
        
        # Styles
        style_heading = styles['Heading1']
        style_heading.alignment = 1 # Center
        style_normal = styles['Normal']
        
        # --- Header Section ---
        store_name = self.config.get('store_name', 'My Store')
        store_addr = self.config.get('store_address', 'Address Line 1\nCity, State - Zip')
        store_gstin = self.config.get('store_gstin', '')
        
        # Store Info (Left) vs Invoice Info (Right)
        # We use a table for layout
        header_data = [
            [Paragraph(f"<b>{store_name}</b>", style_heading), ''],
            [Paragraph(f"{store_addr}<br/>GSTIN: {store_gstin}", style_normal), 
             Paragraph(f"<b>INVOICE NO:</b> {invoice_number}<br/><b>DATE:</b> {buyer_details.get('date', datetime.date.today())}", style_normal)]
        ]
        
        t_header = Table(header_data, colWidths=[100*mm, 80*mm])
        t_header.setStyle(TableStyle([
            ('SPAN', (0,0), (1,0)), # Title spans across
            ('ALIGN', (0,0), (1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,1), (1,1), 'RIGHT'),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("_" * 100, style_normal)) # Horizontal Line
        elements.append(Spacer(1, 10))

        # --- Bill To Section ---
        buyer_name = buyer_details.get('name', 'N/A')
        buyer_contact = buyer_details.get('contact', '')
        
        bill_to_text = f"<b>BILL TO:</b><br/>{buyer_name}<br/>Contact: {buyer_contact}"
        elements.append(Paragraph(bill_to_text, style_normal))
        elements.append(Spacer(1, 15))

        # --- Items Table ---
        # Columns: SN, Item/Model, HSN/SAC, Qty, Rate, Tax%, Tax Amt, Amount
        # Simplified: Item, Model, Rate, Tax, Total
        data = [['SN', 'Model / Description', 'Taxable Val', 'CGST', 'SGST', 'IGST', 'Total']]
        
        grand_total = 0.0
        
        is_interstate = buyer_details.get('is_interstate', False)
        is_inclusive = buyer_details.get('is_tax_inclusive', False)
        default_tax = self.config.get('gst_default_percent', 18.0)
        
        for idx, item in enumerate(items):
            price = float(item.get('price', 0))
            tax_calc = self.calculate_tax(price, default_tax, is_interstate, is_inclusive)
            
            row = [
                str(idx + 1),
                item.get('model', '') + f"\nSN: {item.get('unique_id','')}",
                f"{tax_calc['taxable_value']:.2f}",
                f"{tax_calc['cgst']:.2f}",
                f"{tax_calc['sgst']:.2f}",
                f"{tax_calc['igst']:.2f}",
                f"{tax_calc['total_amount']:.2f}"
            ]
            data.append(row)
            grand_total += tax_calc['total_amount']
            
        # Summary Rows
        data.append(['', 'Subtotal', '', '', '', '', f"{grand_total:.2f}"])
        final_total = grand_total
        
        if discount and discount.get('amount', 0) > 0:
            d_amt = float(discount['amount'])
            d_reason = discount.get('reason', 'Discount')
            data.append(['', f"Less: {d_reason}", '', '', '', '', f"-{d_amt:.2f}"])
            final_total -= d_amt
            
        data.append(['', 'Grand Total', '', '', '', '', f"{final_total:.2f}"])
        
        t = Table(data, colWidths=[10*mm, 60*mm, 25*mm, 20*mm, 20*mm, 20*mm, 30*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), # Grid for items
            ('BOX', (0, 0), (-1, -1), 1, colors.black), # Outer Box
            # Total Row
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.whitesmoke),
        ]))
        
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # --- Footer: Amount in Words & Signatory ---
        # Note: num2words lib would be good here, but standard python only for now.
        
        footer_data = [
            [Paragraph("<b>Terms & Conditions:</b><br/>1. Goods once sold will not be taken back.<br/>2. Warranty as per manufacturer terms.", styles['Normal']),
             Paragraph(f"<br/><br/>_______________________<br/><b>Auth. Signatory</b><br/>For {store_name}", styles['Normal'])]
        ]
        t_footer = Table(footer_data, colWidths=[120*mm, 60*mm])
        t_footer.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
        ]))
        elements.append(t_footer)
        
        doc.build(elements)
        
        if self.activity_logger:
            self.activity_logger.log("INVOICE_GEN", f"Invoice {invoice_number} generated for Rs. {final_total:.2f}")
            
        return True
