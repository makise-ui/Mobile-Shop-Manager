import tkinter as tk
from tkinter import font as tkfont
import re

class MarkdownText(tk.Text):
    """Custom Text widget with Markdown rendering support."""
    
    def __init__(self, parent, **kwargs):
        # Default to word wrap to fix "same line" issues
        if 'wrap' not in kwargs:
            kwargs['wrap'] = tk.WORD
        super().__init__(parent, **kwargs)
        self._setup_styles()
        
    def _setup_styles(self):
        """Configure text tags for markdown rendering."""
        # Heading 1 (# Title)
        self.tag_configure("h1", font=("Segoe UI", 18, "bold"), foreground="#007acc", spacing1=15, spacing3=10)
        
        # Heading 2 (## Subtitle)
        self.tag_configure("h2", font=("Segoe UI", 14, "bold"), foreground="#0078d4", spacing1=12, spacing3=8)
        
        # Heading 3 (### Sub-subtitle)
        self.tag_configure("h3", font=("Segoe UI", 12, "bold"), foreground="#106ebe", spacing1=10, spacing3=6)
        
        # Bold (**text**)
        self.tag_configure("bold", font=("Segoe UI", 10, "bold"))
        
        # Italic (*text*)
        self.tag_configure("italic", font=("Segoe UI", 10, "italic"))
        
        # Code (``text``)
        self.tag_configure("code", font=("Consolas", 9), background="#f0f0f0", foreground="#d73a49")
        
        # Code block (```...```)
        self.tag_configure("codeblock", font=("Consolas", 9), background="#2d2d2d", foreground="#a8ff60", 
                           lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)
        
        # Link [text](url)
        self.tag_configure("link", foreground="#0066cc", underline=True)
        # self.tag_bind("link", "<Button-1>", self._on_link_click) # Removed: Handling per-link in insert
        
        # List item (- text or * text or 1. text)
        self.tag_configure("list", lmargin1=20, lmargin2=40, spacing1=3, spacing3=3)
        
        # Blockquote (> text)
        self.tag_configure("blockquote", font=("Segoe UI", 10, "italic"), foreground="#666666", 
                           lmargin1=20, lmargin2=20, background="#f5f5f5")
        
        # Emphasis (~~text~~)
        self.tag_configure("strikethrough", overstrike=True, foreground="#999999")
        
        # Normal text
        self.tag_configure("normal", font=("Segoe UI", 10), spacing1=2, spacing3=2)
        
        # Special Boxes
        self.tag_configure("example", background="#f0f8ff", foreground="#333333", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5, relief=tk.SOLID, borderwidth=1)
        self.tag_configure("note", background="#fff9e6", foreground="#333333", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5, relief=tk.SOLID, borderwidth=1)
        self.tag_configure("warning", background="#ffe6e6", foreground="#8b0000", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5, relief=tk.SOLID, borderwidth=1)
    
    def insert_markdown(self, index, markdown_text):
        """Parse and insert markdown-formatted text."""
        self.configure(state='normal')
        self.delete("1.0", tk.END)
        
        lines = markdown_text.split('\n')
        in_codeblock = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # --- Code Block ---
            if line_stripped.startswith('```'):
                in_codeblock = not in_codeblock
                continue
            
            if in_codeblock:
                self.insert(tk.END, line + '\n', "codeblock")
                continue
            
            # --- Headings ---
            if line.startswith('# '):
                self.insert(tk.END, line[2:] + '\n', "h1")
                continue
            elif line.startswith('## '):
                self.insert(tk.END, line[3:] + '\n', "h2")
                continue
            elif line.startswith('### '):
                self.insert(tk.END, line[4:] + '\n', "h3")
                continue
            
            # --- Lists ---
            # Bullet: - or *
            if re.match(r'^[\s]*[-*]\s', line):
                content = re.sub(r'^[\s]*[-*]\s', '', line)
                self.insert(tk.END, '• ', "list")
                self._insert_inline_formatted(content + '\n', base_tags=("list",))
                continue
            
            # Numbered: 1.
            elif re.match(r'^[\s]*\d+\.\s', line):
                match = re.match(r'^[\s]*(\d+\.)\s', line)
                if match:
                    number = match.group(1)
                    content = line[match.end():]
                    self.insert(tk.END, f"{number} ", "list")
                    self._insert_inline_formatted(content + '\n', base_tags=("list",))
                    continue

            # --- Blockquotes ---
            if line.startswith('> '):
                content = line[2:]
                tag = "blockquote"
                # Check for special admonitions inside blockquote
                if content.startswith('**Example:**'):
                    tag = "example"
                elif content.startswith('**Note:**'):
                    tag = "note"
                elif content.startswith('**Warning:**'):
                    tag = "warning"
                
                self.insert(tk.END, content + '\n', tag)
                continue
            
            # --- Horizontal Rule ---
            if line_stripped in ['---', '***', '___']:
                self.insert(tk.END, '\n' + ('─' * 40) + '\n', "normal")
                continue

            # --- Normal Text ---
            if line:
                self._insert_inline_formatted(line + '\n', base_tags=("normal",))
            else:
                self.insert(tk.END, '\n', "normal")
        
        self.configure(state='disabled')
    
    def _insert_inline_formatted(self, text, base_tags=()):
        """Handle inline formatting: **bold**, *italic*, `code`, [link](url)"""
        # Regex to tokenize text into (normal, bold, italic, code, link)
        # Priority: Code > Link > Bold > Italic
        token_pattern = r'(`[^`]+`)|(\*\*.*?\*\*)|(\*.*?\*)|(\[.*?\]\(.*?\))'
        
        cursor = 0
        for match in re.finditer(token_pattern, text):
            # 1. Insert text BEFORE match
            pre_text = text[cursor:match.start()]
            if pre_text:
                self.insert(tk.END, pre_text, base_tags)
            
            # 2. Process Match
            token = match.group(0)
            
            if token.startswith('`'): # Code
                self.insert(tk.END, token[1:-1], ("code",) + base_tags)
            
            elif token.startswith('**'): # Bold
                self.insert(tk.END, token[2:-2], ("bold",) + base_tags)
                
            elif token.startswith('*'): # Italic
                self.insert(tk.END, token[1:-1], ("italic",) + base_tags)
                
            elif token.startswith('['): # Link
                # Extract text and url
                m = re.match(r'\[(.*?)\]\((.*?)\)', token)
                if m:
                    label, url = m.groups()
                    # We need a unique tag for this link to bind the URL
                    link_tag = f"link_{len(self.tag_names())}" 
                    self.tag_configure(link_tag, foreground="#0066cc", underline=True)
                    self.tag_bind(link_tag, "<Button-1>", lambda e, u=url: self._open_url(u))
                    self.tag_bind(link_tag, "<Enter>", lambda e: self.config(cursor="hand2"))
                    self.tag_bind(link_tag, "<Leave>", lambda e: self.config(cursor=""))
                    
                    self.insert(tk.END, label, (link_tag,) + base_tags)

            cursor = match.end()
            
        # 3. Insert remaining text
        if cursor < len(text):
            self.insert(tk.END, text[cursor:], base_tags)

    def _open_url(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
        except: pass
