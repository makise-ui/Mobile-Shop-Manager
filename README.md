# 4Bros Mobile Point Manager

A professional Windows desktop application designed for mobile shop inventory management. It streamlines operations by merging stock data from multiple Excel files, providing a unified dashboard, handling GST billing, and offering specialized 2-up barcode printing for thermal printers.

## 🚀 Key Features

- **Unified Inventory Dashboard**: Automatically merges and tracks stock from multiple Excel files. Watches for file changes in real-time.
- **High-Precision Label Printing**: Optimized for **ZPL (Zebra Programming Language)** compatible thermal printers. Supports 2-up label rolls (2 labels per row) with crisp Code128 barcodes.
- **Smart ID Registry**: Assigns a unique 3-character ID to every item. Tracks **Sold** and **Return** status persistently, ensuring data isn't lost when you replace your daily stock sheet.
- **Professional GST Billing**: Generates PDF invoices with automatic CGST/SGST/IGST tax splits.
- **Conflict Resolution**: Detects duplicate entries across different files and helps you resolve them.
- **Customizable**: Configure store details, label dimensions, tax rates, and price markups.

---

## 🛠️ Requirements

- **Operating System**: Windows 10 or Windows 11 (Recommended).
- **Python**: Version 3.10 or higher.
- **Printer**: A thermal label printer (203 DPI recommended) installed as a Windows printer (e.g., Zebra, TSC, Xprinter).

---

## 📥 Installation & Setup

### 1. Install Python
If you haven't already, download and install Python 3.10+ from [python.org](https://www.python.org/downloads/windows/).
*   **Important:** During installation, check the box **"Add Python to PATH"**.

### 2. Get the Code
Download this repository as a ZIP file and extract it, or use git:
```powershell
git clone https://github.com/yourusername/Mobile-Shop-Manager.git
cd Mobile-Shop-Manager
```

### 3. Install Dependencies
Open a Command Prompt or PowerShell in the project folder and run:

```powershell
pip install -r requirements.txt
```

*Note: If you encounter permission errors, try running the command prompt as Administrator.*

### 4. Run the Application
Start the application using:

```powershell
python main.py
```
*(If `python` doesn't work, try `py main.py` or `python3 main.py` depending on your setup).*

---

## 📦 Building a Standalone EXE

To distribute the app to other computers without installing Python, you can package it into a single `.exe` file.

**Note:** The `pyinstaller` command is best run as a module to avoid path issues on Windows.

Run this command in your terminal:

```powershell
python -m PyInstaller --noconfirm --onefile --windowed --name "4BrosManager" --icon "icon.jpg" --hidden-import "PIL._tkinter_finder" --collect-all "escpos" --add-data "core;core" --add-data "gui;gui" --add-data "icon.jpg;." main.py
```

Once finished, you will find `4BrosManager.exe` in the `dist/` folder.

---

## 📂 Data Storage

The application does **not** store your data inside the program folder. Instead, it keeps everything safe in your Documents folder:

`C:\Users\<YourName>\Documents\4BrosManager\`

*   **`config/`**: Contains settings (`config.json`) and file mappings (`file_mappings.json`).
*   **`invoices/`**: Generated PDF bills are saved here.
*   **`id_registry.json`**: The master database of Unique IDs and item statuses. **Back up this file regularly.**

---

## 📚 Documentation

For more detailed instructions, please check the [docs](docs/) folder:

*   [**User Guide**](docs/UserGuide.md): How to use the inventory, billing, and printing features.
*   [**Configuration**](docs/Configuration.md): Advanced settings and file mapping details.
*   [**Troubleshooting**](docs/Troubleshooting.md): Common issues and fixes.

---

## ⚖️ License

**Proprietary Software.** 

Copyright (c) 2026 4Bros Mobile / makise-ui. All rights reserved.

Unauthorized use, copying, modification, or distribution of this software is strictly prohibited without explicit written permission from the owner. See the [LICENSE](LICENSE) file for more details.
