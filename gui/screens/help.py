import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import sys
from pathlib import Path
from ..base import BaseScreen
from ..markdown_renderer import MarkdownText

class HelpScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        # Header Frame
        header_frame = self.add_header("📖 Complete User Guide & Help")
        ttk.Button(header_frame, text="🔄 Reload", command=self._reload_content).pack(side=tk.RIGHT, padx=5)
        ttk.Button(header_frame, text="🔍 Search Help", command=self._search_help).pack(side=tk.RIGHT, padx=5)
        
        # Notebook for sections
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load content from markdown file
        self.markdown_content = self._load_markdown_content()
        
        # 1. Complete Guide (Full Content)
        f_guide = ttk.Frame(self.nb)
        self.nb.add(f_guide, text="📚 Complete Guide")
        self._add_markdown_text(f_guide, self.markdown_content)
        
        # 2. Quick Start
        f_start = ttk.Frame(self.nb)
        self.nb.add(f_start, text="🚀 Quick Start")
        self._add_markdown_text(f_start, self._get_quick_start())
        
        # 3. Features & How-To
        f_feat = ttk.Frame(self.nb)
        self.nb.add(f_feat, text="✨ Core Features")
        self._add_markdown_text(f_feat, self._get_features_guide())
        
        # 4. Keyboard Shortcuts
        f_shortcuts = ttk.Frame(self.nb)
        self.nb.add(f_shortcuts, text="⌨️ Shortcuts")
        self._add_markdown_text(f_shortcuts, self._get_shortcuts())
        
        # 5. Troubleshooting
        f_trouble = ttk.Frame(self.nb)
        self.nb.add(f_trouble, text="🔧 Troubleshooting")
        self._add_markdown_text(f_trouble, self._get_troubleshooting())
        
        # 6. FAQ
        f_faq = ttk.Frame(self.nb)
        self.nb.add(f_faq, text="❓ FAQ")
        self._add_markdown_text(f_faq, self._get_faq_text())

    def navigate_to(self, section_name):
        """Switch to a specific tab by text (partial match)."""
        if not section_name: return
        
        # Normalize
        target = section_name.lower()
        
        for tab_id in self.nb.tabs():
            # Get tab text
            text = self.nb.tab(tab_id, "text").lower()
            if target in text:
                self.nb.select(tab_id)
                return

    def _load_markdown_content(self):
        """Load help content from markdown file if it exists."""
        try:
            # Resolving relative to this file: gui/screens/help.py -> ../../help_content.md
            # But robust way uses sys._MEIPASS or abspath
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys._MEIPASS)
            else:
                base_dir = Path(os.path.abspath(__file__)).parent.parent.parent
                
            help_file = base_dir / "help_content.md"
            if help_file.exists():
                with open(help_file, 'r', encoding='utf-8') as f:
                    return f.read()
        except:
            pass
        # Fallback to basic content
        return self._get_complete_guide()

    def _add_markdown_text(self, parent, content):
        """Add a markdown-rendered text widget."""
        txt = MarkdownText(parent, font=('Segoe UI', 10), wrap=tk.WORD, padx=10, pady=10)
        scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)
        
        txt.insert_markdown("1.0", content)

    def _reload_content(self):
        """Reload content from markdown file."""
        try:
            self.markdown_content = self._load_markdown_content()
            messagebox.showinfo("Reloaded", "Help content reloaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload: {str(e)}")

    def _search_help(self):
        """Search help content."""
        query = simpledialog.askstring("Search Help", "Enter search term:")
        if query:
            query_lower = query.lower()
            matches = []
            for i, line in enumerate(self.markdown_content.split('\n'), 1):
                if query_lower in line.lower():
                    matches.append(f"Line {i}: {line.strip()}")
            
            if matches:
                result = "\n".join(matches[:20])  # Show first 20 matches
                messagebox.showinfo("Search Results", result)
            else:
                messagebox.showinfo("No Results", "No matches found for: " + query)

    def _get_complete_guide(self):
        """Load complete guide - attempts to read from file, falls back to combined content."""
        try:
            # Same logic as load_markdown_content
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys._MEIPASS)
            else:
                base_dir = Path(os.path.abspath(__file__)).parent.parent.parent
            help_file = base_dir / "help_content.md"
            
            if help_file.exists():
                with open(help_file, 'r', encoding='utf-8') as f:
                    return f.read()
        except:
            pass
        return self._get_quick_start() + "\n\n" + self._get_features_guide()

    def _get_quick_start(self):
        return """# 🚀 Quick Start Guide

## Step 1: Initial Setup

### Configure Your Business
1. **First Launch** - Welcome dialog appears
   - Enter your **Store Name** (e.g., "4Bros Mobile Shop")
   - Enter your **Store Address**
   - Enter your **GST Registration Number** (if applicable)

### Add Your Inventory Files
1. Click **Manage** → **Manage Files**
2. Click **+ Add Excel File**
3. Select your stock Excel file (.xlsx, .xls) or CSV
4. Map your columns to the app's fields:
   - Select column for **Model** (e.g., "Mobile Model")
   - Select column for **IMEI** (e.g., "Serial Number")
   - Select column for **Price** (e.g., "Cost Price")
   - Leave unused columns as **(Ignore)**
5. Click **Save Mapping**

> **Example:** Map "Mobile Model" → Model, "Serial Number" → IMEI, "Colour" → Color

## Step 2: Understand the Dashboard

Go to **Inventory** → **Dashboard** to see:
- **Total Items** in stock
- **Total Value** of inventory
- **Est. Profit** (if you set costs)
- **Status Breakdown** (In-Stock / Sold / Returned)
- **Top Models** and **Supplier Distribution**

## Step 3: View Your Inventory

1. Click **Inventory** → **Inventory List**
2. All items from your Excel files displayed in **one unified view**
3. Each item has a **Unique ID** assigned automatically
4. **Search** by Model, IMEI, or Unique ID
5. **Filter** by Status, Price Range, Supplier

## Step 4: Print Labels (Optional)

1. Check **[x]** boxes next to items to print
2. Click **Print Checked**
3. Select printer and mode:
   - **Single Label**: One label per item
   - **2-Up Labels**: Two labels side-by-side (saves paper)
4. Click **Print**

> **Pro Tip:** Labels show **Unique ID** as barcode for fast scanning!

## Step 5: Record Sales

1. Press **F3** or go to **Inventory** → **Quick Status**
2. **Scan** the item's Unique ID (or type it)
3. Select status: **SOLD**, **RETURN**, or **STOCK**
4. If SOLD:
   - Enter **Buyer Name** (from auto-suggest list)
   - Enter **Contact** (optional)
5. Click **Confirm** → Excel updates automatically!

> **Example:**
> - Scan: 1001
> - Status: SOLD
> - Buyer: Rajesh Kumar
> - Contact: 9876543210
> - Result: Item marked SOLD, buyer tracked, Excel file updated

## That's it! You're ready to use the app.

Press **F1** for Search, **F2** for Quick Entry, **F4** for Billing.
"""

    def _get_features_guide(self):
        return """# ✨ Core Features

## 1. Quick Status Update (Fast Scanning)

Perfect for recording sales using a barcode scanner.

**Steps:**
1. Go to **Inventory** → **Quick Status**
2. Scan or type the **Unique ID** or IMEI
3. Select new status: **SOLD**, **RETURN**, or **STOCK**
4. If SOLD:
   - Enter **Buyer Name**
   - Enter **Contact Number** (optional)
5. Click **Confirm**

**Batch Mode:**
- Enable "BATCH MODE" checkbox
- Scan multiple items one after another
- They accumulate in a list
- Review before confirming all at once

> **Example:** Scan 5 phones, all marked SOLD with customer "Rajesh", confirm once.

## 2. Label Printing (Thermal Printers)

Create professional stickers for your items.

**Steps:**
1. Go to **Inventory** → **Inventory List**
2. Check **[x]** boxes for items to print
3. Click **Print Checked**
4. Choose **Printer** and **Mode**:
   - **Single Label**: Standard 50mm × 22mm
   - **2-Up Labels**: Two side-by-side (saves thermal paper)
5. Click **Print**

**Label Contents:**
- Store name
- Scannable barcode (Unique ID)
- Model, Price, RAM/ROM
- Custom notes

> **Pro Tip:** Use **2-Up Mode** to save 50% on thermal paper!

## 3. Advanced Reporting

Create powerful, custom filtered reports to export exactly the data you need.

**Go to:** **Reports** → **Advanced Reporting**

### How it Works
The reporting engine lets you build a "sentence" to describe the items you want. You can stack multiple conditions to narrow down your search.

### 1. Build Your Filters
Click **"+ Add Condition"** to add a rule. A rule has 4 parts:
- **Logic**: How this rule connects to the previous one (AND, OR).
- **Field**: The column to check (e.g., Status, Price, Brand).
- **Operator**: The comparison (e.g., Equals, Contains, Is Empty).
- **Value**: The text or number to match.

**Logic Types Explained:**
- **AND**: *Both* conditions must be true. (Narrower results)
  - *Example:* `Status=IN` **AND** `Price>10000` (Only items that match BOTH)
- **OR**: *Either* condition can be true. (Wider results)
  - *Example:* `Brand=Vivo` **OR** `Brand=Oppo` (Items that are EITHER Vivo OR Oppo)
- **AND NOT**: Exclude specific items.
  - *Example:* `Status=IN` **AND NOT** `Model Contains "Broken"`
- **XOR**: Exclusive OR. One must be true, but not both. (Rarely used)

**Common Operators:**
- **Equals**: Exact match.
- **Contains**: Partial match (e.g., "iPhone" finds "Apple iPhone 13").
- **> / <**: Greater than / Less than (for Price or Dates).
- **Is Empty**: Finds items with missing data (e.g., missing Grade).

### 2. Select Columns to Export
Use the list on the right to choose which fields appear in your Excel/PDF file.
- **Available**: Fields you can add.
- **Selected**: Fields that will be in the report.
- Use **>** and **<** buttons to move fields.
- Drag and drop fields in the "Selected" list to reorder them.

### 3. Sampling (Optional)
Use the "Sampling & Limits" panel to restrict the output:
- **Row Limit**: Only get the top X rows (e.g., top 10 items).
- **Modulo**: Advanced sampling (e.g., every 2nd item).

### 4. Export
- **Preview Data**: See a quick snapshot of the results at the bottom.
- **Export Excel**: Full .xlsx file.
- **Export PDF**: Formatted printable report.

### 💡 Real-World Examples

### Scenario A: High-Value Stock Audit
*Goal: Find all in-stock phones worth more than ₹20,000.*
1. **Condition 1**: `START` | `Status` | `Equals` | `IN`
2. **Condition 2**: `AND` | `Price` | `>` | `20000`

### Scenario B: Sales from Last Week
*Goal: See what sold in the last 7 days.*
1. **Condition 1**: `START` | `Status` | `Equals` | `OUT`
2. **Condition 2**: `AND` | `Date Sold` | `>=` | `Last 7 Days` (Use dropdown)

### Scenario C: Finding "Bad" Data
*Goal: Find items missing a Grade or Supplier.*
1. **Condition 1**: `START` | `Status` | `Equals` | `IN`
2. **Condition 2**: `AND` | `Grade` | `Is Empty` | ``

### Scenario D: Specific Brand Search
*Goal: Find all iPhones (any model).*
1. **Condition 1**: `START` | `Model` | `Contains` | `iPhone`
2. **Condition 2**: `AND` | `Status` | `Equals` | `IN`

> **Pro Tip:** Use the **"💡 Examples"** button in the reporting toolbar to load these presets instantly!

## 4. Invoicing and Billing

Generate professional invoices with GST.

**Steps:**
1. Go to **Billing** → **Billing Screen**
2. **Add Items:**
   - Scan/type Unique ID
   - Item details auto-populate
   - Adjust quantity if needed
3. **Customer Details:**
   - Enter name, address
   - Select or create buyer
4. **Tax Calculation:**
   - Select delivery state
   - GST auto-calculated (CGST+SGST or IGST)
5. **Generate Invoice:**
   - Creates professional PDF
   - Auto-prints (if configured)
   - Saved in Documents/MobileShopManager/Invoices/

**GST Rules:**
- **Intrastate:** CGST (9%) + SGST (9%) = 18%
- **Interstate:** IGST (18%)
- Configurable in Settings

> **Example Invoice:**
> - iPhone 14 (ID: 1001) - ₹65,000
> - Vivo V27 (ID: 1002) - ₹28,000
> - Subtotal: ₹93,000
> - GST (18%): ₹16,740
> - **Total: ₹109,740**

## 5. Analytics and Business Intelligence

Track sales trends and profitability.

**Go to:** **Inventory** → **Analytics**

**View Metrics:**
- Total inventory value
- Estimated profit margin
- Sales velocity (items/day)
- Top suppliers
- Brand distribution

**Price Simulation:**
- Enable in dashboard
- Adjust assumed costs
- See profit impact
- Useful for pricing decisions

**Export Reports:**
- Click **Download Detailed Analytics**
- PDF with charts, tables, sales log
- Includes buyer details and history

## 6. Data Management

Organize your reference data.

**Go to:** **Manage** → **Manage Data**

**Manage Buyers:**
- Add frequent customer names
- Auto-suggest when selling
- Saves typing time

**Manage Colors:**
- Pre-define phone colors
- Ensures data consistency

**Manage Grades:**
- Define condition grades (A1, A2, B1, etc.)
- Track phone quality

---

## Common Workflows

### Daily Stock Entry
1. Update Excel with new phones
2. Press **F5** to refresh
3. Select new items, print labels
4. Affix Unique ID stickers

### Quick Sale
1. Press **F3**
2. Scan barcode
3. Select **SOLD**
4. Enter buyer name
5. Done!

### Monthly Reconciliation
1. **Reports** → **Advanced Reporting**
2. Filter **Status = "IN"**
3. Export to Excel
4. Physical audit against shop stock
"""

    def _get_shortcuts(self):
        return """# ⌨️ Keyboard Shortcuts

## Navigation & Windows

| Shortcut | Action |
|----------|--------|
| **Ctrl+N** or **Ctrl+W** | Open Quick Navigation (Command Palette) |
| **Escape** | Return to Dashboard |
| **Right-Click** | Context menu (copy, edit, delete) |

## Quick Access

| Shortcut | Action |
|----------|--------|
| **F1** | Go to Search Screen |
| **F2** | Go to Quick Entry |
| **F3** | Go to Status Update |
| **F4** | Go to Billing |
| **F5** | Refresh (reload Excel files) |

## In Tables & Lists

| Shortcut | Action |
|----------|--------|
| **Ctrl+C** | Copy selected cell |
| **Ctrl+X** | Cut selected cell |
| **Ctrl+V** | Paste |
| **Delete** | Clear cell |
| **Ctrl+A** | Select all |

---

## Quick Reference Card

```
GLOBAL SHORTCUTS:
  Ctrl+N / Ctrl+W ......... Command Palette
  Escape .................. Dashboard
  Right-Click ............ Context Menu

QUICK ACCESS (Power User):
  F1 ..................... Search
  F2 ..................... Quick Entry
  F3 ..................... Status/Scanning
  F4 ..................... Billing/Invoice
  F5 ..................... Refresh

COMMON WORKFLOWS:
  F3 + Scan + "SOLD" ..... Record sale in 3 seconds
  Ctrl+N + "Print" ...... Open print screen
  F4 + Scan Items ....... Build invoice
```

## Tips for Power Users

- **Batch Scanning:** Enable BATCH MODE in Quick Status, scan multiple items, confirm once
- **Fast Search:** Use **F1** then type model name, results filter in real-time
- **Keyboard Navigation:** Tab through fields instead of mouse clicking
- **Hotkeys Remember:** The app remembers last printer, buyer, etc.
"""

    def _get_troubleshooting(self):
        return """# 🔧 Troubleshooting Guide

## Issue: Excel File Not Updating

**Problem:** Changes in the app don't appear in Excel.

**Solutions:**
1. Ensure Excel file is **CLOSED** (not open in Microsoft Excel)
2. Check file is not **read-only**
3. Verify file path is correct
4. Press **F5** (Manual Refresh) to force reload
5. Check Documents/MobileShopManager/logs/ for errors

> **Pro Tip:** Always close Excel before updating items in the app!

## Issue: Duplicate IMEI Warning

**Problem:** Same IMEI found in multiple files.

**Solution:**
1. **Manage Files** → Review source Excel files
2. Remove actual duplicates from Excel
3. Use app's **Conflict Resolution** to merge
4. Keep the newer/more accurate entry

## Issue: Labels Not Printing

**Problem:** Thermal printer not responding.

**Solutions:**
1. Verify printer is installed and default
2. Test print from Windows (Print Test Page)
3. Check ZPL driver is installed
4. Go to Settings, select correct printer
5. Ensure USB/Network connection active

## Issue: Data Loss After Excel Update

**Problem:** Updated Excel file, lost previous status.

**Solution:**
- Don't worry! Status history stored internally
- Even without Excel, app remembers:
  - Item IDs
  - Who purchased (SOLD status)
  - Buyer information
  - Notes and modifications
- Old data in Activity Log

> **Security Feature:** You never lose sales history!

## Issue: License Activation Failed

**Problem:** Cannot activate license.

**Solutions:**
1. Check internet connection
2. Enter license key exactly (copy-paste recommended)
3. Verify computer online (not offline mode)
4. Check Documents/MobileShopManager/logs/ for details
5. Contact support with log file

## Issue: "Conflict Detected" Warning

**Problem:** Multiple items marked as same ID.

**Explanation:** Same IMEI/item found in different Excel files or rows.

**How to Fix:**
1. **Manage Files** → **Resolve Conflicts**
2. Review both entries
3. Choose which one to keep
4. Duplicate marked as hidden
5. Check source files for actual duplicates

## Issue: Slow Performance

**Problem:** App is slow with large inventory.

**Solutions:**
1. Filter before operating (don't load all 10,000 items)
2. Use presets instead of complex filters
3. Archive old items (mark INACTIVE)
4. Regular cleanup of temporary files
5. Close unnecessary programs for more RAM

## Issue: Lost Configuration

**Problem:** Settings/mappings disappeared.

**Troubleshooting:**
1. Check Documents/MobileShopManager/config/ exists
2. Look in Documents/MobileShopManager/backups/ for old config
3. Re-add Excel files and mapping
4. All status data preserved (no loss)

> **Prevention:** Backup Documents/MobileShopManager/ monthly!

---

## Getting Help

- **Activity Log:** See what the app did recently
- **Error Messages:** Copy exact message
- **Logs:** Check Documents/MobileShopManager/logs/
- **Support:** Provide:
  - Exact error message
  - Steps to reproduce
  - Log file
  - Your configuration (sanitized)
"""

    def _get_faq_text(self):
        return """# ❓ Frequently Asked Questions

## General Questions

### Q: Can I use this on Mac or Linux?

**A:** Currently Windows-only due to ZPL printer integration. Future versions may support other platforms, but thermal printer support would be limited.

### Q: What's the maximum number of items?

**A:** No hard limit. Optimized for 5,000-10,000 items. Larger catalogs (50,000+) need more RAM.

### Q: Can I export my data?

**A:** Yes!
- **Reports** → Export to Excel/PDF
- **Inventory** → Download Full Export
- No vendor lock-in - your data is yours

### Q: What if I lose my Excel files?

**A:** Your data is safe!
- Status history stored internally
- Backup copies in Documents/MobileShopManager/backups/
- Even without Excel, you keep all metadata
- Recreate Excel, app restores references

## Excel and File Management

### Q: My Excel file isn't updating!

**A:** Most common issues:
- Excel file is **OPEN** in Microsoft Excel → Close it
- File is **READ-ONLY** → Remove read-only flag
- File is **LOCKED** by another program → Close that program
- Try pressing **F5** (Manual Refresh) to force reload

> **Best Practice:** Never have Excel open while using the app!

### Q: Can I use multiple Excel files?

**A:** Absolutely! This is a core feature.
1. Add multiple files via **Manage Files**
2. Map columns for each file
3. App automatically merges all data
4. Conflict resolution handles duplicates

### Q: What's the best Excel structure?

**Good Structure:**
```
IMEI | Model | RAM | Price | Supplier | Colour | Status | 
123456789012345 | Vivo V27 | 8GB | 28000 | Distributor A | Blue | | 
987654321098765 | iPhone 14 | 6GB | 65000 | Distributor B | Black | | 
```

**Avoid:**
- Merged cells
- Multiple tables per sheet
- Headers in different rows
- Mixed data types

## Features and Functionality

### Q: How do I change the Store Name on labels?

**A:** Go to **Manage** → **Settings**
- Change **Store Name**
- Change **Label Size**
- Change **GST Rate**

### Q: Can I customize invoice format?

**A:** Partially:
- Change store name, address, GSTIN in Settings
- Add invoice terms
- Future version will support custom templates

### Q: Do you support credit sales?

**A:** Not directly in current version. Workaround:
- Create invoice with payment note
- Mark as SOLD
- Track manually in notes field

### Q: Can I use without Excel?

**A:** You need at least one Excel/CSV file. You can create a simple file with just:
- Model
- IMEI
- Price

Start with one item and build from there.

## Data and Backup

### Q: Where is my data saved?

**A:** All config and history:
- Documents/MobileShopManager/config/ (settings, mappings)
- Documents/MobileShopManager/logs/ (activity log)
- Documents/MobileShopManager/Invoices/ (generated invoices)
- Documents/MobileShopManager/backups/ (Excel backups)

> **Important:** Don't delete the 'config' folder!

### Q: How do I migrate to a new computer?

**A:** 
1. Copy Documents/MobileShopManager/ folder
2. Copy your Excel files
3. Reinstall the app on new computer
4. Point to copied files in **Manage Files**
5. All data, settings, history restored!

### Q: Do you support cloud backup?

**A:** Not built-in, but you can:
- Add Documents/MobileShopManager/ to OneDrive/Google Drive
- Manual weekly backup to USB drive
- Export reports as PDF/Excel

### Q: What's a backup and where are they?

**A:** 
- App creates `.bak` file before every Excel write
- Location: Documents/MobileShopManager/backups/
- Timestamped: YYYYMMDD_HHMMSS format
- If something goes wrong, restore from backup

## Printing and Labels

### Q: Which printers are supported?

**A:** 
- **Zebra/TSC Thermal Printers** (ZPL) - Best support
- **ESC/POS Printers** - Alternative format
- **Standard Windows Printers** - Can print to PDF

### Q: Do I need a thermal printer?

**A:** Not required, but:
- **With thermal printer:** Fast labels, saves paper
- **Without:** Can print to standard printer or PDF
- **2-Up Labels:** Only available with thermal printer

### Q: How do I set default printer?

**A:** 
1. Go to **Manage** → **Settings**
2. Select **Printer Type**
3. Choose default printer
4. Save

## Tips and Best Practices

### Q: How to handle inventory correctly?

**Best Practice:**
1. **Add Excel** with stock data
2. **Print labels** with Unique ID stickers
3. **Affix stickers**

```"""
