import http.server
import socketserver
import threading
import webbrowser
import os
import json
from pathlib import Path

PORT = 8910
DIRECTORY = "zpl_designer"
CONFIG_FILE = "config/custom_template.zpl"
APP_CONFIG_FILE = "config/config.json"

def get_store_name():
    try:
        if os.path.exists(APP_CONFIG_FILE):
            with open(APP_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('store_name', '4 Bros Mobile Point')
    except:
        pass
    return "4 Bros Mobile Point"

class ZPLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/template':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            store_name = get_store_name()
            
            # Default Template with dynamic Store Name
            default_zpl = f"""^XA
^PW400
^LL200
^FO0,10^A0N,30,30^FB400,1,0,C,0^FD{store_name}^FS
^FO95,42^BY3,2,40^BCN,40,N,N,N^FD${{ID}}^FS
^FO330,45^GB50,32,32^FS
^FO330,49^A0N,24,24^FR^FB50,1,0,C,0^FD${{GRADE}}^FS
^FO0,85^A0N,25,25^FB400,1,0,C,0^FD${{ID}}^FS
^FO25,112^A0N,29,29^FB350,2,0,L,0^FD${{MODEL}}^FS
^FO25,145^A0N,26,26^FB200,1,0,L,0^FD${{RAM/ROM}}^FS
^FO150,142^A0N,32,32^FB240,1,0,R,0^FD${{PRICE}}^FS
^XZ"""

            # Load existing if available
            zpl = default_zpl
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r') as f:
                        content = f.read().strip()
                        if len(content) > 10:
                            zpl = content
                except:
                    pass
            
            self.wfile.write(json.dumps({'zpl': zpl, 'store_name': store_name}).encode())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/save':
            length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(length))
            zpl = data.get('zpl', '')
            
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                f.write(zpl)
                
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Saved")
        else:
            self.send_error(404)

_server_thread = None

def start_server():
    global _server_thread
    if _server_thread: return
    
    def run():
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", PORT), ZPLHandler) as httpd:
            print(f"ZPL Designer running at http://localhost:{PORT}")
            httpd.serve_forever()

    _server_thread = threading.Thread(target=run, daemon=True)
    _server_thread.start()

def open_designer():
    start_server()
    webbrowser.open(f"http://localhost:{PORT}")
