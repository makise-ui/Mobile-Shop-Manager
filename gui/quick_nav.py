import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb

class QuickNavOverlay(tk.Toplevel):
    def __init__(self, parent, screens_map, callback):
        super().__init__(parent)
        self.parent = parent
        self.screens = screens_map # Dict: {'key': 'Label'}
        self.callback = callback
        
        # Window Setup
        self.overrideredirect(True) # Frameless
        self.attributes('-alpha', 0.95) # Slight Transparency
        self.attributes('-topmost', True)
        
        # Center on parent
        w, h = 800, 500
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.configure(bg="#2b2b2b")
        
        self.selected_index = 0
        self.items = list(self.screens.items()) # List of (key, label)
        
        # Calculate Grid Layout
        self.cols = 3
        self.rows = (len(self.items) + self.cols - 1) // self.cols
        
        self._init_ui()
        self._bind_keys()
        
        # Force focus
        self.focus_set()
        self.grab_set()

    def _init_ui(self):
        # Container
        self.container = tk.Frame(self, bg="#2b2b2b")
        self.container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Title
        tk.Label(self.container, text="Quick Navigation", font=('Segoe UI', 20, 'bold'), 
                 fg="white", bg="#2b2b2b").pack(pady=(0, 20))
        
        # Scrollable Area
        self.canvas = tk.Canvas(self.container, bg="#2b2b2b", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#2b2b2b")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.cards = []
        
        # Icons Mapping
        icon_map = {
            'dashboard': '📊', 'inventory': '📱', 'billing': '🧾',
            'quick_entry': '⚡', 'search': '🔍', 'status': '📋',
            'analytics': '📈', 'invoices': '📂', 'designer': '🏷️',
            'files': '📁', 'managedata': '💾', 'settings': '⚙️',
            'edit': '✏️', 'help': '❓'
        }
        
        for idx, (key, label) in enumerate(self.items):
            r = idx // self.cols
            c = idx % self.cols
            
            # Card Frame
            f = tk.Frame(self.scrollable_frame, bg="#444", width=220, height=140)
            f.grid(row=r, column=c, padx=15, pady=15)
            f.pack_propagate(False)
            
            # Inner Container for centering
            inner = tk.Frame(f, bg="#444")
            inner.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            
            # Icon
            ico_char = icon_map.get(key, '🔹')
            l_ico = tk.Label(inner, text=ico_char, font=('Segoe UI Emoji', 32), fg="#ccc", bg="#444")
            l_ico.pack()
            
            # Text
            l_txt = tk.Label(inner, text=label, font=('Segoe UI', 12, 'bold'), fg="#ccc", bg="#444")
            l_txt.pack(pady=(5, 0))
            
            # Store reference
            self.cards.append({'frame': f, 'icon': l_ico, 'label': l_txt, 'row': r})
            
            # Click Interaction
            for w in [f, inner, l_ico, l_txt]:
                w.bind("<Button-1>", lambda e, k=key: self._confirm(k))

        self._update_selection()

    def _update_selection(self):
        for i, card in enumerate(self.cards):
            if i == self.selected_index:
                # Highlight
                bg_col = "#007acc"
                fg_col = "white"
                card['frame'].config(bg=bg_col, highlightbackground="white", highlightthickness=2)
                card['icon'].config(bg=bg_col, fg=fg_col)
                card['label'].config(bg=bg_col, fg=fg_col)
                self._ensure_visible(i)
            else:
                # Normal
                bg_col = "#444"
                fg_col = "#ccc"
                card['frame'].config(bg=bg_col, highlightthickness=0)
                card['icon'].config(bg=bg_col, fg=fg_col)
                card['label'].config(bg=bg_col, fg=fg_col)

    def _ensure_visible(self, index):
        # Precise scroll to item
        row = self.cards[index]['row']
        # Height of card (120) + padding (30) = 150 approx
        card_h = 150
        
        # Canvas Height
        canvas_h = self.canvas.winfo_height()
        if canvas_h <= 10: canvas_h = 500 # Fallback if not rendered yet
        
        # Target Y position (Top of the row)
        target_y = row * card_h
        
        # Current Scroll Position (0.0 to 1.0)
        scroll_pos = self.canvas.yview()[0]
        
        # Total Scrollable Height
        total_h = self.rows * card_h
        if total_h == 0: return
        
        current_top_y = scroll_pos * total_h
        current_bottom_y = current_top_y + canvas_h
        
        # Check if out of view
        if target_y < current_top_y:
            # Scroll Up
            new_pos = max(0, target_y / total_h)
            self.canvas.yview_moveto(new_pos)
        elif (target_y + card_h) > current_bottom_y:
            # Scroll Down
            new_pos = max(0, (target_y - canvas_h + card_h) / total_h)
            self.canvas.yview_moveto(new_pos)

    def _bind_keys(self):
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<Up>", self._move_selection)
        self.bind("<Down>", self._move_selection)
        self.bind("<Left>", self._move_selection)
        self.bind("<Right>", self._move_selection)
        self.bind("<FocusOut>", lambda e: self.destroy())

    def _move_selection(self, event):
        key = event.keysym
        if key == 'Right':
            self.selected_index = (self.selected_index + 1) % len(self.items)
        elif key == 'Left':
            self.selected_index = (self.selected_index - 1) % len(self.items)
        elif key == 'Down':
            new = self.selected_index + self.cols
            if new < len(self.items): self.selected_index = new
        elif key == 'Up':
            new = self.selected_index - self.cols
            if new >= 0: self.selected_index = new
            
        self._update_selection()

    def _select_item(self, index):
        self.selected_index = index
        self._update_selection()

    def _confirm(self, key=None):
        target_key = key if key else self.items[self.selected_index][0]
        self.callback(target_key)
        self.destroy()
