# 4bros Mobile Point Manager

A professional Windows desktop application for managing mobile shop inventory, printing 2-up barcode labels, and generating GST invoices.

## 🚀 Key Features

- **Inventory Dashboard**: Combined view of stock from multiple Excel files with real-time file watching.
- **2-Up ZPL Printing**: Optimized for thermal printers with 2-label rows. Features high-quality Code128 barcodes and precise alignment.
- **ID Lookup (Search)**: Instantly find any phone by its unique ID to view full details (Buy/Sell Price, IMEI, Supplier, Color).
- **Professional GST Billing**: Generate neat PDF invoices with CGST/SGST/IGST splits, customer contact info, and tax-inclusive toggles.
- **Color Management**: Preload and manage mobile colors for consistent data entry.
- **Persistent Status**: Mark items as **SOLD** or **RTN** (Return) directly in the app; status persists even after Excel reloads.
- **Auto-Price Markup**: Set a percentage (e.g., 15%) in settings to automatically calculate selling prices.

## 🛠️ Requirements

- **OS**: Windows 10 or 11
- **Python**: 3.10+ (for source execution)
- **Dependencies**: pandas, openpyxl, Pillow, python-barcode, reportlab, python-escpos, pywin32.

## 📥 Installation (Source)

1. Clone the repository or extract the source folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python main.py
   ```

## 📦 Packaging (Create .EXE)

To build a standalone `.exe` for Windows, use the following command:

```bash
pyinstaller --noconfirm --onefile --windowed --name "4BrosManager" --icon "icon.jpg" --hidden-import "PIL._tkinter_finder" --collect-all "escpos" --add-data "core;core" --add-data "gui;gui" --add-data "icon.jpg;." main.py
```

## 📂 Data & Configuration

For safety, the app stores all settings, ID history, and file mappings in your Windows Documents folder:
`C:\Users\<YourUser>\Documents\4BrosManager\config\`

- **`config.json`**: Store name, label sizes, GST %, and Markup %.
- **`id_registry.json`**: Permanent record of IDs and Status (Sold/Return). **Do not delete this file if you want to keep your ID history.**
- **`file_mappings.json`**: Remembers which Excel columns match the app fields.

## 📝 Usage Tips

1. **Adding Files**: Use the "Manage Files" screen to add your Excel/CSV. Map the columns once, and the app will remember them.
2. **Printing**: Check the items you want to print in the Inventory screen. The "Print Checked" button will show a **2-up Preview** before sending to the printer.
3. **ZPL Support**: The app is optimized for Zebra/ZPL compatible thermal printers (203 DPI). Set your ZPL printer as the Windows Default.