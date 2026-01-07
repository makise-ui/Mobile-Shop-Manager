import os
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PIL import Image

# Try importing win32 libraries, handle failure for non-Windows dev env
try:
    import win32print
    import win32api
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

    def get_system_printers(self):
        if not HAS_WIN32:
            return []
        try:
            # Enum local and network printers
            printers = []
            # Level 2 returns (ServerName, PrinterName, ShareName, PortName, DriverName, Comment, Location, DevMode, SepFile, PrintProcessor, Datatype, Parameters, Attributes, Priority, DefaultPriority, StartTime, UntilTime, Status, cJobs, AveragePPM)
            # Actually EnumPrinters(flags, level)
            # Level 2 is details. Level 4 is usually used for simple enumeration but typically Level 2 with LOCAL|CONNECTIONS is best.
            # win32print.PRINTER_ENUM_LOCAL = 2
            # win32print.PRINTER_ENUM_CONNECTIONS = 4
            
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            for p in win32print.EnumPrinters(flags):
                # p[2] is usually printer name in Level 2? 
                # Docs: Level 1: (flags, desc, name, comment) -> name is p[2]
                # Docs: Level 2: (server, printer, share, ...) -> printer is p[1]
                # Let's check what EnumPrinters defaults to or just try/except
                # Actually default level is often 1. 
                # Let's stick to safe retrieval.
                name = p[2] # Typically Name
                if name:
                    printers.append(name)
            return sorted(list(set(printers)))
        except Exception as e:
            print(f"Error listing printers: {e}")
            return []

    def print_pdf(self, pdf_path, printer_name):
        if not HAS_WIN32:
            print("Cannot print PDF: Win32 not available.")
            return False
            
        try:
            # Use ShellExecute 'printto' verb
            # This requires a PDF reader (like Adobe or Sumatra) to be registered for 'printto'
            # Most modern Windows setups have this.
            win32api.ShellExecute(0, "printto", pdf_path, f'"{printer_name}"', ".", 0)
            return True
        except Exception as e:
            print(f"PDF Print Error: {e}")
            return False

    def send_raw_zpl(self, zpl_string, printer_name=None):
        """Sends raw ZPL string directly to the printer."""
        if not HAS_WIN32:
            print("Win32 not available for printing.")
            return False

        try:
            if not printer_name:
                try:
                    printer_name = win32print.GetDefaultPrinter()
                except:
                    return False

            encoded_zpl = zpl_string.encode("utf-8")
            h_printer = win32print.OpenPrinter(printer_name)
            try:
                job_info = win32print.StartDocPrinter(h_printer, 1, ("RawZPL", None, "raw"))
                if job_info:
                    win32print.StartPagePrinter(h_printer)
                    win32print.WritePrinter(h_printer, encoded_zpl)
                    win32print.EndPagePrinter(h_printer)
                    win32print.EndDocPrinter(h_printer)
            finally:
                win32print.ClosePrinter(h_printer)
            return True
        except Exception as e:
            print(f"Raw Print Error: {e}")
            return False

    def print_label_zpl(self, item_data, printer_name=None):
        if not HAS_WIN32:
            return False

        try:
            if not printer_name:
                try:
                    printer_name = win32print.GetDefaultPrinter()
                except:
                    return False

            # Load Custom Template if exists
            template_path = self.config.get_config_dir() / "custom_template.zpl"
            zpl_template = ""
            
            if os.path.exists(template_path):
                try:
                    with open(template_path, 'r') as f:
                        zpl_template = f.read()
                except Exception as e:
                    print(f"Template load error: {e}")

            store_name = self.config.get('store_name', '4 Bros Mobile')[:20]
            uid = str(item_data.get('unique_id', ''))
            model = item_data.get('model', '')[:25]
            ram_rom = item_data.get('ram_rom', '')
            price = f"Rs. {item_data.get('price', 0):,.0f}"
            grade = str(item_data.get('grade', '')).upper()
            
            # Helper for conditional Grade ZPL
            grade_zpl = ""
            if grade:
                grade_zpl = f"^FO330,45^GB50,32,32^FS\n^FO330,49^A0N,24,24^FR^FB50,1,0,C,0^FD{grade}^FS"

            if zpl_template and len(zpl_template) > 10:
                # Use Template with Variable Injection
                # We use simple string replace or format map. 
                # Our designer uses ${variable} syntax.
                
                # Dictionary of available variables
                vars_map = {
                    "${store_name}": store_name,
                    "${id}": uid,
                    "${model}": model,
                    "${ram_rom}": ram_rom,
                    "${price}": price,
                    "${grade}": grade,
                    "${imei}": str(item_data.get('imei', '')),
                }
                
                zpl = zpl_template
                for k, v in vars_map.items():
                    zpl = zpl.replace(k, v)
                    
            else:
                # Fallback to Hardcoded logic
                zpl = f"""
^XA
^PW400
^LL176
^FO0,10^A0N,30,30
^FB400,1,0,C,0^FD{store_name}^FS

^FO95,42^BY3,2,40^BCN,40,N,N,N
^FD{uid}^FS

{grade_zpl}

^FO0,85^A0N,25,25
^FB400,1,0,C,0^FD{uid}^FS

^FO25,112^A0N,29,29
^FB350,2,0,L,0^FD{model}^FS

^FO25,145^A0N,26,26
^FB200,1,0,L,0^FD{ram_rom}^FS

^FO150,142^A0N,32,32
^FB240,1,0,R,0^FD{price}^FS

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
        
        # Load Template logic
        template_path = self.config.get_config_dir() / "custom_template.zpl"
        zpl_template = None
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r') as f:
                    zpl_template = f.read()
            except Exception as e:
                print(f"Template load error: {e}")

        count = 0
        try:
            h_printer = win32print.OpenPrinter(printer_name)
            
            # Process in pairs
            for i in range(0, len(items), 2):
                item1 = items[i]
                item2 = items[i+1] if i+1 < len(items) else None
                
                if zpl_template and len(zpl_template) > 10:
                    # USE TEMPLATE
                    zpl_content = zpl_template
                    
                    # Prepare Variables
                    store = self.config.get('store_name', '4 Bros Mobile')[:20]
                    
                    # Helper to map item to prefix
                    def get_vars(itm, suffix=""):
                        if not itm:
                            return {
                                f"${{store_name{suffix}}}": "",
                                f"${{id{suffix}}}": "",
                                f"${{model{suffix}}}": "",
                                f"${{ram_rom{suffix}}}": "",
                                f"${{price{suffix}}}": "",
                                f"${{grade{suffix}}}": "",
                                f"${{imei{suffix}}}": ""
                            }
                            
                        return {
                            f"${{store_name{suffix}}}": store,
                            f"${{id{suffix}}}": str(itm.get('unique_id', '')),
                            f"${{model{suffix}}}": itm.get('model', '')[:25],
                            f"${{ram_rom{suffix}}}": itm.get('ram_rom', ''),
                            f"${{price{suffix}}}": f"Rs. {itm.get('price', 0):,.0f}",
                            f"${{grade{suffix}}}": str(itm.get('grade', '')).upper(),
                            f"${{imei{suffix}}}": str(itm.get('imei', ''))
                        }

                    # Map Left (No suffix) and Right (_2 suffix)
                    vars_map = get_vars(item1, "")
                    vars_map.update(get_vars(item2, "_2"))
                    
                    for k, v in vars_map.items():
                        zpl_content = zpl_content.replace(k, v)

                else:
                    # FALLBACK TO HARDCODED
                    zpl_content = "^XA^PW830^LL176"
                    
                    def get_fields(item, is_right_side):
                        store = self.config.get('store_name', '4 Bros Mobile')[:20]
                        uid = str(item.get('unique_id', ''))
                        model = item.get('model', '')[:25]
                        ram = item.get('ram_rom', '')
                        pr = f"Rs. {item.get('price', 0):,.0f}"
                        grade = str(item.get('grade', '')).upper()

                        if not is_right_side:
                            # LEFT SIDE
                            grade_zpl = ""
                            if grade:
                                grade_zpl = f"^FO330,45^GB50,32,32^FS\n^FO330,49^A0N,24,24^FR^FB50,1,0,C,0^FD{grade}^FS"
                            
                            return f"""
^FX --- LEFT SIDE: {model} (ID {uid}) --- ^FS
^FO0,10^A0N,30,30
^FB400,1,0,C,0^FD{store}^FS

^FO95,42^BY3,2,40^BCN,40,N,N,N
^FD{uid}^FS

{grade_zpl}

^FO0,85^A0N,25,25
^FB400,1,0,C,0^FD{uid}^FS

^FO25,112^A0N,29,29
^FB350,2,0,L,0^FD{model}^FS

^FO25,145^A0N,26,26
^FB200,1,0,L,0^FD{ram}^FS

^FO150,142^A0N,32,32
^FB240,1,0,R,0^FD{pr}^FS
"""
                        else:
                            # RIGHT SIDE
                            grade_zpl = ""
                            if grade:
                                grade_zpl = f"^FO740,45^GB50,32,32^FS\n^FO740,49^A0N,24,24^FR^FB50,1,0,C,0^FD{grade}^FS"

                            return f"""
^FX --- RIGHT SIDE: {model} (ID {uid}) --- ^FS
^FO416,10^A0N,30,30
^FB400,1,0,C,0^FD{store}^FS

^FO511,42^BY3,2,40^BCN,40,N,N,N
^FD{uid}^FS

{grade_zpl}

^FO416,85^A0N,25,25
^FB400,1,0,C,0^FD{uid}^FS

^FO441,112^A0N,29,29
^FB350,2,0,L,0^FD{model}^FS

^FO441,145^A0N,26,26
^FB200,1,0,L,0^FD{ram}^FS

^FO566,142^A0N,32,32
^FB240,1,0,R,0^FD{pr}^FS
"""
                    
                    # Add Label 1 (Left)
                    zpl_content += get_fields(item1, False)
                    
                    # Add Label 2 (Right) if exists
                    if item2:
                        zpl_content += get_fields(item2, True)
                    
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
