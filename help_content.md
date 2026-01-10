# Mobile Shop Manager - Complete User Guide

## 🚀 Getting Started

### Step 1: Initial Setup

Before you can start managing your inventory, you need to configure the application with your business details.

1. **First Launch**
   - The application will show a Welcome dialog
   - Enter your Store Name (e.g., "4Bros Mobile Shop")
   - Enter your Store Address
   - Enter your GST Registration Number (if applicable)

2. **Add Your Inventory Files**
   - Click **Manage** → **Manage Files** in the main navigation
   - Click **+ Add Excel File**
   - Select your stock Excel file (.xlsx, .xls) or CSV file
   - The application will display available columns in your file

3. **Map Your Columns**
   - The app needs to understand your column names
   - For each canonical field (IMEI, Model, Price, etc.), select the matching column from your file
   - If you don't have a column, select **(Ignore)**
   - Set a default **Supplier** name for this file
   - Click **Save Mapping** when done

> **Example:** If your Excel has columns: "Mobile Model", "Serial Number", "Cost Price", "Colour"
> - Map "Mobile Model" → Model
> - Map "Serial Number" → IMEI
> - Map "Cost Price" → Price
> - Map "Colour" → Color
> - Leave others as (Ignore)

### Step 2: Understanding the Dashboard

After loading your files, go to **Inventory** → **Dashboard** to see:

- **Total Items**: Count of all in-stock items
- **Total Value**: Sum of all item prices
- **Est. Profit**: Estimated profit (if you set cost prices)
- **Status Breakdown**: Items split by In-Stock / Sold / Returned
- **Top Models**: Most common phone models in your inventory
- **Supplier Distribution**: Items grouped by supplier

### Step 3: Working with Your Inventory

1. **View Full Inventory**
   - Click **Inventory** → **Inventory List**
   - All items from your Excel files are displayed in one unified view
   - Each item has a **Unique ID** (assigned automatically by the system)

2. **Search and Filter**
   - Use the search box to find items by:
     - **Model** (e.g., "Vivo V27")
     - **IMEI** (e.g., "123456789012345")
     - **Unique ID** (e.g., "MSM001234")
   - Use **Filter** button for advanced searches

3. **Understand Item Status**
   - **IN**: Item is in stock and available
   - **OUT**: Item has been sold
   - **RTN**: Item has been returned
   - The system tracks all status changes automatically

---

## 📋 Core Features

### 1. Quick Status Update (Fast Scanning)

**Perfect for:** Recording sales quickly using a barcode scanner

1. Go to **Inventory** → **Quick Status**
2. Scan or type the **Unique ID** (or IMEI)
3. Select new status: **SOLD**, **RETURN**, or **STOCK**
4. If SOLD:
   - Enter **Buyer Name** (select from list or type new)
   - Enter **Contact** (optional)
5. Click **Confirm**
6. The app updates your Excel file automatically!

> **Example:** 
> - Scan: 1001
> - Status: SOLD
> - Buyer: Rajesh
> - Contact: 9876543210
> - Result: Item 1001 is marked SOLD, buyer tracked, Excel updated

**Batch Mode:**
- Enable "BATCH MODE" checkbox
- Scan multiple phones one after another
- They accumulate in a waiting list
- Review before confirming all at once

### 2. Label Printing (Thermal Printers)

**Perfect for:** Creating stickers for your items using thermal printers

1. Go to **Inventory** → **Inventory List**
2. Check the **[x]** boxes next to items you want to print
3. Click **Print Checked**
4. Select **Printer** and **Mode**:
   - **Single Label**: One label per page (50mm × 22mm standard)
   - **2-Up Labels**: Two labels side-by-side (saves thermal paper)
5. Click **Print**

**Label Layout:**
- Header: Your store name
- Barcode: Unique ID (scannable)
- Details: Model, Price, RAM/ROM
- Footer: Optional notes

> **Pro Tip:** Use ZPL Designer to customize label layout!

### 3. Advanced Reporting

**Perfect for:** Creating filtered reports and exporting data

1. Go to **Reports** → **Advanced Reporting**
2. **Create Filters:**
   - Add conditions like: Status = "IN" AND Price > 15,000
   - Combine multiple filters (AND/OR logic)
3. **Select Columns:**
   - Choose which columns to display in the report
   - Drag to reorder
4. **Export Options:**
   - **Excel**: .xlsx file with filtered data
   - **PDF**: Professional report with formatting
   - **Word**: .docx file for further editing
5. **Save as Preset:**
   - Save your filter configuration for quick reuse
   - Example presets: "In-Stock Premium", "Budget Phones", "Recent Sales"

> **Example Filter:**
> - Condition 1: Status = "IN"
> - Condition 2: Price ≥ 20,000
> - Condition 3: Model contains "Vivo"
> - Export as Excel to get all premium Vivo phones in stock

### 4. Invoicing and Billing

**Perfect for:** Creating professional invoices with tax calculations

1. Go to **Billing** → **Billing Screen**
2. **Add Items:**
   - Scan/type the Unique ID
   - Item details appear automatically
   - Adjust quantity if needed
3. **Customer Details:**
   - Enter customer name
   - Enter address
   - Select or create buyer profile
4. **Tax Information:**
   - Select delivery state (auto-calculates tax)
   - System calculates CGST + SGST or IGST automatically
5. **Generate Invoice:**
   - Click **Generate Invoice**
   - Invoice is saved as PDF and automatically printed
   - Saved in Documents/MobileShopManager/Invoices/

> **Example Invoice:**
> - Item 1: iPhone 14 (ID: 1001) - ₹65,000
> - Item 2: Vivo V27 (ID: 1002) - ₹28,000
> - Subtotal: ₹93,000
> - GST (18%): ₹16,740
> - **Total: ₹109,740**

**GST Calculation Rules:**
- **Intrastate (within same state):** CGST (9%) + SGST (9%)
- **Interstate (different state):** IGST (18%)
- **GST Rate:** Configurable in Settings (default 18%)

### 5. Analytics and Business Intelligence

**Perfect for:** Tracking sales trends and profitability

1. Go to **Inventory** → **Analytics**
2. **View Metrics:**
   - Total inventory value
   - Estimated profit margin
   - Sales velocity (items sold per day)
   - Top-performing suppliers
   - Brand distribution

3. **Price Simulation:**
   - Enable simulation mode in dashboard
   - Adjust assumed costs
   - See impact on profit calculations
   - Useful for price planning

4. **Export Reports:**
   - Click **Download Detailed Analytics**
   - Get PDF with charts, tables, and full sales log
   - Includes buyer details and transaction history

### 6. Data Management

**Perfect for:** Organizing your reference data

1. Go to **Manage** → **Manage Data**
2. **Manage Buyers:**
   - Add frequently used buyer names
   - Auto-suggest when selling
   - Saves typing time
3. **Manage Colors:**
   - Pre-define available colors for quick selection
   - Ensures consistency in data entry
4. **Manage Grades:**
   - Define phone condition grades (A1, A2, B1, etc.)
   - Use for quality tracking

---

## ⌨️ Keyboard Shortcuts (Power User Guide)

| Shortcut | Action |
|----------|--------|
| **Ctrl+N** or **Ctrl+W** | Open Quick Navigation (Command Palette) |
| **F1** | Go to Search Screen |
| **F2** | Go to Quick Entry Screen |
| **F3** | Go to Status Update Screen |
| **F4** | Go to Billing Screen |
| **F5** | Manual Refresh (reload Excel files) |
| **Escape** | Return to Dashboard |
| **Right-Click** | Context menu (copy, edit, delete) |

---

## 🔍 Search and Navigation

### Quick Search

1. Use the search box on any inventory screen
2. Type to filter by:
   - **Model**: "Vivo", "iPhone", "Samsung"
   - **IMEI**: "123456", partial matches work
   - **ID**: Item's unique ID
   - **Supplier**: Supplier name
3. Results update in real-time

### Advanced Search (F1)

1. Press **F1** or go to **Inventory** → **Search**
2. Multiple filter options:
   - **Status**: Filter by IN/OUT/RTN
   - **Price Range**: Min and max price
   - **Supplier**: Select specific supplier
   - **Date Range**: Items added in timeframe
3. Combine multiple filters
4. Click **Search** to apply

> **Example:**
> - Status = IN
> - Price Range: 10,000 - 25,000
> - Supplier = "Distributor A"
> - Result: All in-stock phones from Distributor A priced 10-25K

---

## 📱 Excel File Management

### Adding Multiple Files

1. Go to **Manage** → **Manage Files**
2. You can add multiple Excel files from different suppliers
3. The system **automatically merges** them
4. **Conflict Resolution:** If same IMEI appears in multiple files:
   - System alerts you
   - Choose which one to keep or merge
   - Duplicate is marked as hidden

### Watching Files for Changes

- The app **automatically watches** your Excel files
- If you update an Excel file externally:
  - Changes are detected
  - Inventory automatically refreshes
  - No manual import/export needed
- **Note:** Close the Excel file first (don't edit while app is open)

### Backup and Safety

- Every time the app writes to your Excel file, it creates a backup
- Backups stored in: Documents/MobileShopManager/backups/
- Backups are timestamped (YYYYMMDD_HHMMSS format)
- If Excel is locked: App warns instead of crashing

---

## 🎨 Customization and Settings

### Theme and Appearance

1. Go to **Manage** → **Settings**
2. **Theme**: Select light/dark themes (Cosmo, Darkly, etc.)
3. **Font Size**: Adjust UI text size
4. **Store Name**: Change your business name (appears on labels)
5. **Store Address**: For invoices

### Label Configuration

1. **Label Size**: Default 50mm × 22mm for standard thermal printers
2. **Printer Type**: 
   - Windows (ZPL): Best for Zebra/TSC thermal printers
   - ESC/POS: Alternative format for some printers
3. **2-Up Printing**: Enable for side-by-side labels

### GST Configuration

1. Go to **Settings** → **Billing**
2. **GST Rate**: Default 18% (adjust for your state)
3. **Store GSTIN**: Your 15-digit GST number
4. **Invoice Terms**: Custom terms to print on invoices

### ZPL Template Designer

1. Go to **Tools** → **ZPL Designer** (if available)
2. **Drag-and-drop** fields onto template:
   - Store name
   - Barcode
   - Model
   - Price
   - Custom text
3. **Preview** in real-time
4. **Save** custom template
5. Use in label printing

---

## 🛠️ Troubleshooting

### Issue: Excel File Not Updating

**Problem:** Changes in the app don't appear in Excel.

**Solutions:**
1. Ensure Excel file is **CLOSED** (not open in Microsoft Excel)
2. Check file permissions (file should not be read-only)
3. Verify the file path is correct
4. Try **F5** (Manual Refresh) to force reload
5. Check Documents/MobileShopManager/logs/ for error messages

### Issue: Duplicate IMEI Warning

**Problem:** Same IMEI found in multiple files.

**Solution:**
1. Go to **Manage** → **Manage Files**
2. Review your source Excel files for actual duplicates
3. Remove duplicates from source files
4. In the app, use conflict resolution to merge them
5. Keep the newer/more accurate entry

### Issue: Labels Not Printing

**Problem:** Thermal printer not responding.

**Solutions:**
1. Verify printer is installed and set as default
2. Test print from Windows (Print Test Page)
3. Check ZPL printer driver is installed
4. Go to Settings and select correct printer
5. Ensure USB/Network connection is active

### Issue: Data Loss After Excel Update

**Problem:** Updated Excel file, lost previous status updates.

**Solution:**
- Don't worry! The app maintains **persistent registry**
- Status changes (SOLD, RETURNED) are stored internally
- Even if you replace Excel file, app remembers:
  - Item IDs
  - Status history
  - Buyer information
  - Notes and modifications
- Old data still accessible in Activity Log

> **Security Feature:** This ensures you never lose sales history even if source files change!

### Issue: License Activation Failed

**Problem:** Cannot activate license.

**Solutions:**
1. Ensure you have internet connection
2. Enter license key exactly as provided (copy-paste recommended)
3. Verify computer is not in offline mode
4. Check Documents/MobileShopManager/logs/ for details
5. Contact support with the log file

---

## 💡 Tips and Best Practices

### Excel File Best Practices

**Good Excel Structure:**
```
| IMEI | Model | RAM | Storage | Price | Supplier | Status |
| 123456789012345 | Vivo V27 | 8GB | 128GB | 28000 | Distributor A | |
| 987654321098765 | iPhone 14 | 6GB | 128GB | 65000 | Distributor B | |
```

**Avoid:**
- Merged cells
- Multiple tables in one sheet
- Headers in different rows
- Mixed data types in columns

### Efficient Labeling

1. **Batch print** all items at once
2. Use **2-up mode** to save thermal paper
3. Print to PDF first to **preview** before printing
4. Keep **backup physical copies** of labels

### Sales Tracking

1. Always use **Quick Status** when selling
2. Enter buyer name for **repeat customer tracking**
3. Scan unique ID (faster than IMEI) 
4. Regular reports help identify:
   - Slow-moving inventory
   - Popular brands
   - Peak sales periods

### Backup Strategy

1. **Weekly backup** your Excel files to cloud storage
2. Keep Documents/MobileShopManager/ in cloud sync (Google Drive, OneDrive)
3. Export **monthly reports** for accounting
4. Backup before major Excel file changes

---

## 📊 Keyboard Shortcut Reference Card

```
Navigation & Windows:
  Ctrl+N / Ctrl+W    Open Command Palette
  Escape             Go to Dashboard
  Right-Click        Context Menu

Quick Access:
  F1                 Search Screen
  F2                 Quick Entry
  F3                 Status Update
  F4                 Billing
  F5                 Refresh

In Tables:
  Ctrl+C             Copy selected cell
  Ctrl+X             Cut selected cell
  Ctrl+V             Paste
  Delete             Clear cell
```

---

## 🎓 Common Workflows

### Workflow 1: Daily Stock Entry

1. **Morning:** Check your Excel for new items
2. **Update Excel:** Add new phones with IMEI, Model, Price
3. **Refresh App:** Press F5 or restart
4. **Print Labels:** Select new items, print stickers
5. **Affix Labels:** Put stickers on phones with Unique ID visible

### Workflow 2: Quick Sale

1. **Press F3** (Quick Status)
2. **Scan barcode** on phone label
3. **Select SOLD**
4. **Enter buyer name** (from auto-suggest)
5. **Confirm** → Done! Excel updates automatically

### Workflow 3: Monthly Reconciliation

1. **Go to Reports** → **Advanced Reporting**
2. **Filter:** Status = "IN" (in-stock items)
3. **Export to Excel** for physical verification
4. **Physical audit:** Count items in shop
5. **Mark discrepancies** in the app

### Workflow 4: Generate Invoice

1. **Go to Billing**
2. **Scan multiple items** to add to cart
3. **Verify quantities and prices**
4. **Enter customer details**
5. **Generate Invoice** → Automatic PDF + Print
6. **Hand over** professional receipt to customer

---

## 🔐 Data and Security

### Where Your Data is Stored

- **Config Files:** Documents/MobileShopManager/config/
- **Activity Logs:** Documents/MobileShopManager/logs/
- **Invoices:** Documents/MobileShopManager/Invoices/
- **Backups:** Documents/MobileShopManager/backups/
- **Item Metadata:** Stored in id_registry.json (persistent)

### Privacy and Confidentiality

- All data is stored **locally** on your computer
- No cloud upload unless explicitly enabled
- GST numbers and buyer details are **encrypted**
- Only you have access to your business data

### Backup Recommendations

1. **Local backup:** Windows File History or Similar
2. **Cloud backup:** OneDrive, Google Drive (optional)
3. **External drive:** Monthly data export
4. **Regular exports:** Save reports as PDF/Excel

---

## 📞 Support and Feedback

### Getting Help

- Check the **FAQ** tab in this help screen
- Review **Activity Log** for recent actions
- Check Documents/MobileShopManager/logs/ for errors
- Contact support at **hasanfq818@gmail.com** with:
  - Exact error message
  - Step-by-step reproduction steps
  - Log file (logs/)

### Reporting Issues

- Clear description of the problem
- Screenshot if applicable
- Relevant Excel file structure (sanitized)
- Your configuration details
- Email to: **hasanfq818@gmail.com**

### Feature Requests

- Describe desired functionality
- Explain business benefit
- Provide examples/use cases
- Vote on existing feature requests
- Send to: **hasanfq818@gmail.com**

---

## ❓ Frequently Asked Questions

### Q: Can I use this on Mac or Linux?

**A:** The current version is Windows-only due to ZPL printer integration and Win32 API dependency. A future version may support other platforms, but thermal printer support would be limited.

### Q: What's the maximum number of items?

**A:** No hard limit, but performance optimizes for 5,000-10,000 items. Larger catalogs (50,000+) may need more RAM.

### Q: Can I export my data?

**A:** Yes! 
- Reports → Export to Excel/PDF
- Inventory → Download Full Export
- All data exported without vendor lock-in

### Q: What if I lose my Excel files?

**A:** Your data is safe!
- Status history stored in internal registry
- Backup copies exist in backups/
- Even without Excel, you keep all metadata
- Recreate Excel file, app will restore references

### Q: How do I migrate to new computer?

**A:** 
1. Copy Documents/MobileShopManager/ folder to new computer
2. Copy your Excel files
3. Reinstall the app
4. Point to copied files in Manage → Manage Files
5. All previous data, settings, history restored

### Q: Is there a portable/USB version?

**A:** Not currently. The app requires Documents folder for data persistence. Future version may support portable mode.

### Q: Can I customize the invoice format?

**A:** Partially:
- Change store name, address, GSTIN in Settings
- Add invoice terms
- Future version will support custom templates

### Q: Do you support credit sales?

**A:** Not directly in current version. Workaround:
- Create invoice with payment notes
- Mark as SOLD
- Track manually in notes field

---

## 🚀 Advanced Features

### Batch Operations

- Select multiple items with checkboxes
- Right-click for bulk actions:
  - **Change Status** (all to SOLD)
  - **Change Supplier** (for inventory reorganization)
  - **Add Tags** (custom grouping)
  - **Delete Entries** (archive old items)

### Custom Filters and Presets

1. **Save filter presets:**
   - Create a filter (Status=IN, Price>20K)
   - Save as "Premium In-Stock"
   - Reuse with one click

2. **Combine filters:**
   - IN Stock + Distributor A + Vivo brand
   - Shows exactly what you need

### Integration with External Tools

- **Export to Excel:** Full compatibility with all versions
- **Print to PDF:** Use any PDF printer
- **Email invoices:** Save PDF, send via email client
- **Accounting software:** Export CSV for import

---

## 📈 Performance Optimization

### For Large Inventories

1. **Filter before printing** (don't print 10,000 items)
2. **Use presets** instead of creating complex filters
3. **Archive old items** (mark as INACTIVE)
4. **Regular cleanup** of temporary files
5. **Backup and restore** periodically

### Speeding Up Search

1. Use **Unique ID** (faster than IMEI)
2. **Avoid wildcards** in filters
3. **Set auto-refresh interval** higher (in Settings)
4. **Close other programs** for more RAM

---

**Last Updated:** 2026-01-10
**Version:** 1.4.0
**Support:** Contact hasanfq818@gmail.com

