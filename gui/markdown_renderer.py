import tkinter as tk
from tkinter import font as tkfont
import re

class MarkdownText(tk.Text):
    """Custom Text widget with Markdown rendering support."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._setup_styles()
        
    def _setup_styles(self):
        """Configure text tags for markdown rendering."""
        # Heading 1 (# Title)
        self.tag_configure("h1", font=("Segoe UI", 18, "bold"), foreground="#007acc", spacing1=10, spacing3=10)
        
        # Heading 2 (## Subtitle)
        self.tag_configure("h2", font=("Segoe UI", 14, "bold"), foreground="#0078d4", spacing1=8, spacing3=8)
        
        # Heading 3 (### Sub-subtitle)
        self.tag_configure("h3", font=("Segoe UI", 12, "bold"), foreground="#106ebe", spacing1=6, spacing3=6)
        
        # Bold (**text**)
        self.tag_configure("bold", font=("Segoe UI", 10, "bold"))
        
        # Italic (*text*)
        self.tag_configure("italic", font=("Segoe UI", 10, "italic"))
        
        # Code (``text``)
        self.tag_configure("code", font=("Courier New", 9), background="#f0f0f0", foreground="#d73a49", relief=tk.SUNKEN, borderwidth=1)
        
        # Code block (```...```)
        self.tag_configure("codeblock", font=("Courier New", 9), background="#2d2d2d", foreground="#a8ff60", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)
        
        # Link [text](url)
        self.tag_configure("link", foreground="#0066cc", underline=True)
        self.tag_bind("link", "<Button-1>", self._on_link_click)
        
        # List item (- text or * text or 1. text)
        self.tag_configure("list", lmargin1=30, lmargin2=30)
        
        # Blockquote (> text)
        self.tag_configure("blockquote", font=("Segoe UI", 10, "italic"), foreground="#666666", lmargin1=30, lmargin2=30, background="#f5f5f5")
        
        # Emphasis (~~text~~)
        self.tag_configure("strikethrough", overstrike=True, foreground="#999999")
        
        # Normal text
        self.tag_configure("normal", font=("Segoe UI", 10))
        
        # Example box
        self.tag_configure("example", background="#f0f8ff", foreground="#333333", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5, relief=tk.SOLID, borderwidth=1)
        
        # Tip/Note box
        self.tag_configure("note", background="#fff9e6", foreground="#333333", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5, relief=tk.SOLID, borderwidth=1)
        
        # Warning box
        self.tag_configure("warning", background="#ffe6e6", foreground="#8b0000", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5, relief=tk.SOLID, borderwidth=1, font=("Segoe UI", 10, "bold"))
    
    def insert_markdown(self, index, markdown_text):
        """Parse and insert markdown-formatted text."""
        self.configure(state='normal')
        self.delete("1.0", tk.END)
        
        lines = markdown_text.split('\n')
        in_codeblock = False
        codeblock_buffer = []
        in_example = False
        in_note = False
        in_warning = False
        
        for line in lines:
            # Code block handling (``` ... ```)
            if line.strip().startswith('```'):
                if in_codeblock:
                    # End code block
                    self.insert(tk.END, '\n'.join(codeblock_buffer) + '\n', "codeblock")
                    self.insert(tk.END, '\n')
                    codeblock_buffer = []
                    in_codeblock = False
                else:
                    # Start code block
                    in_codeblock = True
                continue
            
            if in_codeblock:
                codeblock_buffer.append(line)
                continue
            
            # Special blocks
            if line.strip().startswith('> **Example:**'):
                in_example = True
                self.insert(tk.END, '📝 Example:\n', ("example", "bold"))
                continue
            elif line.strip().startswith('> **Note:**'):
                in_note = True
                self.insert(tk.END, '💡 Note:\n', ("note", "bold"))
                continue
            elif line.strip().startswith('> **Warning:**'):
                in_warning = True
                self.insert(tk.END, '⚠️  Warning:\n', ("warning", "bold"))
                continue
            
            if in_example or in_note or in_warning:
                if line.strip() == '':
                    in_example = in_note = in_warning = False
                    self.insert(tk.END, '\n')
                    continue
                else:
                    tag = "example" if in_example else ("note" if in_note else "warning")
                    self.insert(tk.END, line + '\n', tag)
                    continue
            
            # Headings
            if line.startswith('# '):
                self.insert(tk.END, line[2:] + '\n', "h1")
                continue
            elif line.startswith('## '):
                self.insert(tk.END, line[3:] + '\n', "h2")
                continue
            elif line.startswith('### '):
                self.insert(tk.END, line[4:] + '\n', "h3")
                continue
            
            # Blockquotes (> text)
            if line.startswith('> '):
                self.insert(tk.END, line[2:] + '\n', "blockquote")
                continue
            
            # Lists (-, *, or number.)
            if re.match(r'^[\s]*[-*]\s', line):
                self.insert(tk.END, '• ', "list")
                self._insert_inline_formatted(line.lstrip('-* '))
                continue
            elif re.match(r'^[\s]*\d+\.\s', line):
                match = re.match(r'^[\s]*(\d+)\.\s', line)
                if match:
                    self.insert(tk.END, match.group(1) + '. ', "list")
                    remaining = line[match.end():]
                    self._insert_inline_formatted(remaining)
                    continue
            
            # Regular text with inline formatting
            if line.strip():
                self._insert_inline_formatted(line)
            
            self.insert(tk.END, '\n')
        
        self.configure(state='disabled')
    
    def _insert_inline_formatted(self, text):
        """Handle inline formatting: **bold**, *italic*, `code`, [link](url), ~~strikethrough~~"""
        # Pattern: **bold**, *italic*, `code`, ~~strikethrough~~, [link](url)
        pattern = r'(\*\*.*?\*\*|\*.*?\*|`.*?`|~~.*?~~|\[.*?\]\(.*?\))'
        
        last_end = 0
        for match in re.finditer(pattern, text):
            # Insert normal text before match
            if match.start() > last_end:
                self.insert(tk.END, text[last_end:match.start()], "normal")
            
            matched = match.group(0)
            
            # Bold
            if matched.startswith('**') and matched.endswith('**'):
                self.insert(tk.END, matched[2:-2], "bold")
            # Italic
            elif matched.startswith('*') and matched.endswith('*'):
                self.insert(tk.END, matched[1:-1], "italic")
            # Code
            elif matched.startswith('`') and matched.endswith('`'):
                self.insert(tk.END, matched[1:-1], "code")
            # Strikethrough
            elif matched.startswith('~~') and matched.endswith('~~'):
                self.insert(tk.END, matched[2:-2], "strikethrough")
            # Link
            elif matched.startswith('[') and '](' in matched:
                link_match = re.match(r'\[(.*?)\]\((.*?)\)', matched)
                if link_match:
                    self.insert(tk.END, link_match.group(1), "link")
                    self.tag_configure("link", data=link_match.group(2))
            
            last_end = match.end()
        
        # Insert remaining text
        if last_end < len(text):
            self.insert(tk.END, text[last_end:], "normal")
    
    def _on_link_click(self, event):
        """Handle link clicks."""
        try:
            import webbrowser
            index = self.index(f"@{event.x},{event.y}")
            # This is a simplified version; actual link extraction would be more complex
            webbrowser.open("https://github.com/makise-ui/Mobile-Shop-Manager")
        except:
            pass
