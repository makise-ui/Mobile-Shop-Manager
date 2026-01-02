# 4 Bros Mobile Manager

Desktop application for managing mobile inventory, printing barcode labels, and generating GST invoices.

## Requirements
- Windows 10/11
- Python 3.10+
- Excel (for reading .xlsx files)
- Thermal Printer (optional, for labels)

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

## Packaging (Windows EXE)

To create a standalone executable:

```bash
pyinstaller --onefile --windowed --name "4BrosManager" --add-data "core;core" --add-data "gui;gui" main.py
```

## Features
- **File Watching**: Automatically updates inventory when Excel files change.
- **Mapping**: Map your Excel columns to app fields (IMEI, Model, Price, etc.).
- **Labels**: Preview and print Code128 barcodes.
- **Billing**: Generate GST invoices (CGST/SGST/IGST).
