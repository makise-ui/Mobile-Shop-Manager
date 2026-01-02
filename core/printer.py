import os
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PIL import Image

# Try importing win32 libraries, handle failure for non-Windows dev env
try:
    import win32print
    import win32ui
    from PIL import ImageWin
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# Try importing escpos
try:
    from escpos.printer import Usb, Serial, Network
    HAS_ESCPOS = True
except ImportError:
    HAS_ESCPOS = False

class PrinterManager:
    def __init__(self, config_manager, barcode_generator):
        self.config = config_manager
        self.barcode_gen = barcode_generator

    def print_label_zpl(self, item_data, printer_name=None):
        if not HAS_WIN32:
            return False

        try:
            if not printer_name:
                try:
                    printer_name = win32print.GetDefaultPrinter()
                except:
                    return False

            # ZPL Template (203 DPI, 400 dots width approx 50mm)
            # Adjust ^PW based on config if needed, but 400 is standard for 2 inch width
            
            store_name = self.config.get('store_name', '4 Bros Mobile')[:20]
            uid = str(item_data.get('unique_id', ''))
            model = item_data.get('model', '')[:25]
            ram_rom = item_data.get('ram_rom', '')
            price = f"Rs. {item_data.get('price', 0):,.0f}"
            
            # ZPL Template Optimized for 50mm x 22mm (approx 400x176 dots at 203 DPI)
            # Coordinates are tight.
            # Header: Y=5
            # Barcode: Y=35, H=40
            # ID: Y=80
            # Model: Y=105
            # RAM/ROM: Y=135
            # Price: Y=135 (Right aligned)
            
            zpl = f"""
^XA
^PW400
^LL176
^FO0,5^A0N,20,20
^FB400,1,0,C,0^FD{store_name}^FS

^FO50,30^BY2,2,40^BCN,40,N,N,N
^FD{uid}^FS

^FO0,75^A0N,18,18
^FB400,1,0,C,0^FD{uid}^FS

^FO10,100^A0N,18,18
^FB280,2,0,L,0^FD{model}^FS

^FO10,140^A0N,18,18
^FB200,1,0,L,0^FD{ram_rom}^FS

^FO200,135^A0N,25,25
^FB190,1,0,R,0^FD{price}^FS

^XZ
"""
            # Send Raw ZPL
            encoded_zpl = zpl.encode("utf-8")
            h_printer = win32print.OpenPrinter(printer_name)
            try:
                job_info = win32print.StartDocPrinter(h_printer, 1, ("LabelZPL", None, "raw"))
                if job_info:
                    win32print.StartPagePrinter(h_printer)
                    win32print.WritePrinter(h_printer, encoded_zpl)
                    win32print.EndPagePrinter(h_printer)
                    win32print.EndDocPrinter(h_printer)
            finally:
                win32print.ClosePrinter(h_printer)
                
            return True
        except Exception as e:
            print(f"ZPL Print Error: {e}")
            return False

    def _calculate_barcode_x(self, data, column_center_x, module_width=2):
        """
        Calculates X position to center Code 128 barcode.
        Formula: 35 overhead + 11 per char (Subset B).
        """
        data_str = str(data)
        total_modules = 35 + (11 * len(data_str))
        barcode_width_dots = total_modules * module_width
        start_x = column_center_x - (barcode_width_dots / 2)
        return int(start_x)

    def print_batch_zpl(self, items, printer_name=None):
        if not HAS_WIN32:
            return 0

        if not printer_name:
            try:
                printer_name = win32print.GetDefaultPrinter()
            except:
                return 0
        
        count = 0
        try:
            h_printer = win32print.OpenPrinter(printer_name)
            
            # Process in pairs
            for i in range(0, len(items), 2):
                item1 = items[i]
                item2 = items[i+1] if i+1 < len(items) else None
                
                zpl_content = "^XA^PW830^LL176" 
                
                def get_fields(item, x_offset):
                    store = self.config.get('store_name', '4bros mobile')[:20]
                    uid = str(item.get('unique_id', ''))
                    model = item.get('model', '')[:25]
                    ram = item.get('ram_rom', '')
                    pr = f"Rs. {item.get('price', 0):,.0f}"
                    
                    # Calculate Dynamic Barcode Center
                    center_x = x_offset + 200
                    bc_x = self._calculate_barcode_x(uid, center_x)
                    
                    return f"""
^FO{x_offset+0},5^A0N,28,28
^FB400,1,0,C,0^FD{store}^FS

^FO{bc_x},35^BY2,2,40^BCN,40,N,N,N
^FD{uid}^FS

^FO{x_offset+0},80^A0N,22,22
^FB400,1,0,C,0^FD{uid}^FS

^FO{x_offset+10},105^A0N,22,22
^FB280,2,0,L,0^FD{model}^FS

^FO{x_offset+10},145^A0N,22,22
^FB200,1,0,L,0^FD{ram}^FS

^FO{x_offset+150},140^A0N,30,30
^FB230,1,0,R,0^FD{pr}^FS
"""
                
                # Add Label 1 (Left)
                zpl_content += get_fields(item1, 0)
                
                # Add Label 2 (Right) if exists
                if item2:
                    # Offset 416 dots (approx 52mm start point)
                    # Gap between labels is handled by skipping pixels or physical gap
                    # Assuming 50mm label + 2mm gap -> Start next at 52mm (416 dots)
                    zpl_content += get_fields(item2, 416)
                
                zpl_content += "^XZ"
                
                # Send Job
                win32print.StartDocPrinter(h_printer, 1, ("BatchLabel", None, "raw"))
                win32print.StartPagePrinter(h_printer)
                win32print.WritePrinter(h_printer, zpl_content.encode("utf-8"))
                win32print.EndPagePrinter(h_printer)
                win32print.EndDocPrinter(h_printer)
                
                count += (2 if item2 else 1)
                
            win32print.ClosePrinter(h_printer)
            return count
            
        except Exception as e:
            print(f"Batch Print Error: {e}")
            return 0

    def print_label_windows(self, item_data, printer_name=None):
        # Prefer ZPL if configured or default to it for thermal
        # For now, let's just use ZPL if the user wants it. 
        # But to be safe, I'll check config.
        if self.config.get('printer_type') == 'zpl':
            return self.print_label_zpl(item_data, printer_name)
            
        w_mm = self.config.get('label_width_mm')
        h_mm = self.config.get('label_height_mm')
        
        # 1. Generate Image
        try:
            img = self.barcode_gen.generate_label_preview(item_data, w_mm, h_mm, dpi=203)
        except Exception as e:
            print(f"Error generating label image: {e}")
            return False

        # 2. Try Printing (Windows)
        if HAS_WIN32:
            try:
                if not printer_name:
                    try:
                        printer_name = win32print.GetDefaultPrinter()
                    except:
                        # Fallback: Pick first available
                        printers = [p[2] for p in win32print.EnumPrinters(2)]
                        if printers:
                            printer_name = printers[0]
                        else:
                            raise Exception("No printers found")
                
                print(f"Attempting to print to: {printer_name}")
                
                hDC = win32ui.CreateDC()
                hDC.CreatePrinterDC(printer_name)
                hDC.StartDoc("Label Print")
                hDC.StartPage()
                
                dib = ImageWin.Dib(img)
                dib.draw(hDC.GetHandleOutput(), (0, 0, img.size[0], img.size[1]))
                
                hDC.EndPage()
                hDC.EndDoc()
                hDC.DeleteDC()
                print("Print job sent successfully.")
                return True
            except Exception as e:
                print(f"Windows Print Failed: {e}")
                # Fallthrough to fallback
        else:
             print("win32print not available.")
        
        # 3. Fallback: Save to file (Mock Printer)
        self._save_debug_print(img, item_data.get('unique_id', 'unknown'))
        return True

    def _save_debug_print(self, img, uid):
        debug_dir = "debug_prints"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        # Timestamp to avoid overwrite
        ts = int(datetime.datetime.now().timestamp())
        fname = f"{debug_dir}/label_{uid}_{ts}.png"
        img.save(fname)
        print(f"Printer unavailable. Label saved to {fname}")

    def print_label_escpos(self, item_data):
        if not HAS_ESCPOS:
            print("ESC/POS library not found.")
            return False
        
        # This requires specific printer config (VID/PID for USB, IP for Network)
        # For this prototype, we'll assume a dummy or mock unless configured
        # Real implementation needs a config UI for printer connection
        print("ESC/POS printing triggered (Stub).")
        return True

    def export_labels_pdf(self, items, filename):
        """
        items: list of item_data dicts
        filename: output path
        """
        w_mm = self.config.get('label_width_mm')
        h_mm = self.config.get('label_height_mm')
        
        # A4 Page setup or Custom Label Roll?
        # Requirement says "Batch print... arrange as per label sheet"
        # Let's assume A4 sheet with grid for now
        
        c = canvas.Canvas(filename)
        # Simple flow: fill page
        
        page_w, page_h = 210*mm, 297*mm
        c.setPageSize((page_w, page_h))
        
        x_start = 10*mm
        y_start = page_h - 10*mm - (h_mm*mm)
        x, y = x_start, y_start
        
        for item in items:
            # Generate temp image
            # ReportLab can insert images
            img = self.barcode_gen.generate_label_preview(item, w_mm, h_mm, dpi=300)
            img_path = f"temp_lbl_{item['unique_id']}.png"
            img.save(img_path)
            
            c.drawImage(img_path, x, y, width=w_mm*mm, height=h_mm*mm)
            os.remove(img_path) # Cleanup
            
            # Move Cursor
            x += (w_mm + 2)*mm
            if x + w_mm*mm > page_w - 10*mm:
                x = x_start
                y -= (h_mm + 2)*mm
            
            if y < 10*mm:
                c.showPage()
                y = y_start
                x = x_start
                
        c.save()
        return True
