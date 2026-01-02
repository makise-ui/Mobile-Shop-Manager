import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io

class BarcodeGenerator:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
    def generate_barcode_image(self, data):
        """Generates a Code128 barcode image in memory."""
        # Code128 is versatile
        CODE128 = barcode.get_barcode_class('code128')
        # Use ImageWriter to render as image, keeping it minimal (no text usually, we render text manually)
        writer = ImageWriter()
        
        # Ensure data is string
        data = str(data)
        
        rv = io.BytesIO()
        code = CODE128(data, writer=writer)
        code.write(rv, options={"write_text": False, "quiet_zone": 1.0, "module_height": 8.0})
        rv.seek(0)
        
        return Image.open(rv)

    def generate_label_preview(self, item_data, width_mm=50, height_mm=22, dpi=203):
        """
        Generates the full label image preview.
        item_data: dict with model, ram_rom, price, unique_id
        dpi: 203 is standard for thermal printers
        """
        # Convert mm to pixels
        width_px = int((width_mm / 25.4) * dpi)
        height_px = int((height_mm / 25.4) * dpi)
        
        img = Image.new('RGB', (width_px, height_px), 'white')
        draw = ImageDraw.Draw(img)
        
        # Load fonts - fallback to default if specific ttf not available
        try:
            font_header = ImageFont.truetype("arial.ttf", int(height_px * 0.15))
            font_model = ImageFont.truetype("arial.ttf", int(height_px * 0.12))
            font_price = ImageFont.truetype("arialbd.ttf", int(height_px * 0.15)) # Bold
        except:
            font_header = ImageFont.load_default()
            font_model = ImageFont.load_default()
            font_price = ImageFont.load_default()

        # 1. Header: "4 Bros Mobile"
        header_text = self.config_manager.get('store_name', "4 Bros Mobile")
        # Centered
        # bbox = draw.textbbox((0, 0), header_text, font=font_header)
        # text_w = bbox[2] - bbox[0]
        # For simplicity in Pillow < 10 (older) or safest:
        # text_w, text_h = draw.textsize(header_text, font=font_header) 
        # But assuming recent Pillow:
        text_w = draw.textlength(header_text, font=font_header)
        draw.text(((width_px - text_w) / 2, 2), header_text, fill='black', font=font_header)
        
        # 2. Barcode
        barcode_val = item_data.get('unique_id', '00000')
        bc_img = self.generate_barcode_image(barcode_val)
        
        # Resize barcode to fit middle section
        # target width: 80% of label
        # target height: 40% of label
        bc_w_target = int(width_px * 0.8)
        bc_h_target = int(height_px * 0.4)
        bc_img = bc_img.resize((bc_w_target, bc_h_target))
        
        # Paste centered
        bc_x = int((width_px - bc_w_target) / 2)
        bc_y = int(height_px * 0.20)
        img.paste(bc_img, (bc_x, bc_y))
        
        # ID Text below barcode
        id_text = str(barcode_val)
        # Use small font
        font_id = ImageFont.truetype("arial.ttf", int(height_px * 0.10)) if 'arial.ttf' in self.config_manager.get('font', '') else ImageFont.load_default()
        
        # Center ID
        id_w = draw.textlength(id_text, font=font_id)
        draw.text(((width_px - id_w) / 2, bc_y + bc_h_target), id_text, fill='black', font=font_id)
        
        # 3. Model & RAM/ROM (Bottom Left)
        model_text = item_data.get('model', 'Unknown')[:15] # Truncate if long
        ram_rom_text = item_data.get('ram_rom', '')
        
        y_text_start = int(height_px * 0.70)
        draw.text((5, y_text_start), model_text, fill='black', font=font_model)
        draw.text((5, y_text_start + int(height_px * 0.12)), ram_rom_text, fill='black', font=font_model)
        
        # 4. Price (Bottom Right)
        price_val = float(item_data.get('price', 0))
        price_text = f"₹{price_val:,.0f}"
        
        # Right align
        p_len = draw.textlength(price_text, font=font_price)
        draw.text((width_px - p_len - 5, y_text_start + 5), price_text, fill='black', font=font_price)
        
        return img
