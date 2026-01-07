import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import ttkbootstrap as tb
import sys

class LicenseDialog(tk.Toplevel):
    def __init__(self, parent, license_manager, on_success):
        super().__init__(parent)
        self.title("Product Activation")
        self.geometry("600x450")
        self.lic_mgr = license_manager
        self.on_success = on_success
        
        # Lock window
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.resizable(False, False)
        # self.transient(parent) # Removed to prevent issues with hidden parent
        self.attributes("-topmost", True) # Force on top
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Center
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        self._init_ui()
        
    def _init_ui(self):
        hw_id = self.lic_mgr.get_hardware_id()
        
        # Header
        ttk.Label(self, text="License Activation Required", font=('Segoe UI', 16, 'bold'), foreground="red").pack(pady=(20, 10))
        
        ttk.Label(self, text="This software is locked to this specific computer.", font=('Segoe UI', 10)).pack()
        ttk.Label(self, text="Please send the Hardware ID below to the administrator to receive your key.", font=('Segoe UI', 10)).pack(pady=(0, 20))
        
        # Hardware ID Section
        f_id = ttk.LabelFrame(self, text="Your Hardware ID", padding=15)
        f_id.pack(fill=tk.X, padx=30, pady=5)
        
        self.ent_id = ttk.Entry(f_id, font=('Consolas', 11, 'bold'), state='readonly')
        self.ent_id.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Insert ID
        self.ent_id.config(state='normal')
        self.ent_id.insert(0, hw_id)
        self.ent_id.config(state='readonly')
        
        btn_copy = ttk.Button(f_id, text="📋 Copy ID", command=lambda: self.copy_to_clipboard(hw_id), bootstyle="info-outline")
        btn_copy.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Key Entry Section
        f_key = ttk.LabelFrame(self, text="Enter License Key", padding=15)
        f_key.pack(fill=tk.X, padx=30, pady=15)
        
        self.var_key = tk.StringVar()
        self.ent_key = ttk.Entry(f_key, textvariable=self.var_key, font=('Consolas', 12), justify='center')
        self.ent_key.pack(fill=tk.X)
        self.ent_key.focus_set()
        
        # Activate Button
        ttk.Button(self, text="UNLOCK SOFTWARE", bootstyle="success", command=self.activate, width=20).pack(pady=20)
        
    def activate(self):
        key = self.var_key.get()
        if not key:
            messagebox.showwarning("Input Required", "Please enter a license key.")
            return
            
        if self.lic_mgr.validate_license(key):
            try:
                self.lic_mgr.save_license(key)
                
                # Check for Initial Setup (Names)
                config = self.lic_mgr.config
                curr_store = config.get('store_name', 'My Mobile Shop')
                curr_app = config.get('app_display_name', 'Mobile Shop Manager')
                
                # If defaults detected, prompt user
                is_default = (curr_store in ["My Mobile Shop", "4bros Mobile Point"]) or \
                             (curr_app in ["Mobile Shop Manager", "4 Bros Mobile Manager"])
                             
                if is_default:
                    messagebox.showinfo("Welcome", "Activation Successful!\nLet's set up your business details.")
                    
                    # 1. App Name
                    new_app = simpledialog.askstring("Setup (1/2)", "Enter Application Title:\n(e.g., 'Kevin's Manager')")
                    if new_app and new_app.strip():
                        config.set('app_display_name', new_app.strip())
                        
                    # 2. Store Name
                    new_store = simpledialog.askstring("Setup (2/2)", "Enter Shop Name for Bills/Labels:\n(e.g., 'Kevin Mobile Shop')")
                    if new_store and new_store.strip():
                        config.set('store_name', new_store.strip())
                    
                    config.save_config()
                
                else:
                    messagebox.showinfo("Activation Successful", "Thank you for your purchase!\nThe software is now activated.")
                
                self.destroy()
                self.on_success() # Call main app starter
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}")
        else:
            messagebox.showerror("Activation Failed", "Invalid License Key.\nPlease verify the key with the administrator.")

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update() # Required for clipboard to finalize
        messagebox.showinfo("Copied", "Hardware ID copied to clipboard.")

    def on_close(self):
        # If they close the dialog without activating, kill everything
        if messagebox.askyesno("Exit", "Exit application?"):
            self.master.destroy()
            sys.exit(0)
