# 4Bros Mobile Point Manager

## Project Overview
**4Bros Mobile Point Manager** is a Windows desktop application designed for mobile shop inventory management. It aggregates stock data from multiple Excel files, provides a unified dashboard, handles GST billing, and features specialized 2-up barcode printing using ZPL commands for thermal printers.

**Key Goals:**
- **Inventory Unification:** Merges data from diverse Excel sources into a single view.
- **Efficient Labeling:** High-speed, 2-up ZPL printing for retail tagging.
- **Sales & Returns:** Tracks item status (Sold/Return) persistently, even if the source Excel files are replaced.
- **GST Billing:** Generates professional invoices with tax calculations.

## Architecture

The project follows a modular Python structure using `Tkinter` for the GUI and `Pandas` for data processing.

### Directory Structure
- **`main.py`**: Application entry point. Initializes the GUI loop.
- **`core/`**: Business logic and backend services.
    - **`inventory.py`**: Core engine. Loads Excel files, applies column mappings, normalizes data, and merges it with the persistent `IDRegistry`.
    - **`printer.py`**: Handles printing operations. Supports **ZPL (Zebra Programming Language)** via raw Win32 spooler for thermal printers and GDI printing for standard printers.
    - **`config.py`**: Manages application settings and file mappings. Stores data in `Documents/4BrosManager/config/`.
    - **`id_registry.py`**: Maintains persistent metadata (Unique IDs, Status, Custom Notes) to ensure data continuity across Excel file updates.
    - **`billing.py`**: Logic for tax calculations and invoice generation.
- **`gui/`**: Tkinter-based user interface.
    - **`app.py`**: Main window and layout orchestration.
    - **`screens.py`**: Individual UI screens (Inventory, Billing, Settings).
    - **`dialogs.py`**: Popups for mappings, conflicts, and confirmations.
- **`utils/`**: Helper utilities.

### Key Technical Decisions
- **Data Persistence**: configuration and persistent metadata (like "Sold" status) are stored in JSON files within the user's `Documents` folder, not the application directory. This ensures data safety during updates.
- **Excel Normalization**: The app allows users to map their specific Excel column names (e.g., "M.O.P." -> "price") to internal canonical fields.
- **ZPL Printing**: Uses raw printer commands (`win32print.WritePrinter`) to send ZPL code directly to thermal printers, ensuring high precision and alignment that image-based printing lacks.

## Development Conventions

### Environment & Dependencies
- **Python Version**: 3.10+
- **OS**: Windows (Primary target due to `pywin32` usage).
- **Key Libraries**:
    - `pandas`, `openpyxl`: Data manipulation.
    - `tk`: GUI Framework.
    - `pywin32`: Windows API integration for printing.
    - `reportlab`: PDF Invoice generation.
    - `python-barcode`, `Pillow`: Barcode image generation.

### Code Style
- **Error Handling**: Critical OS-dependent imports (like `win32print`) are wrapped in `try-except` blocks to allow development on non-Windows systems (though functionality will be limited).
- **Paths**: Uses `pathlib` for robust path handling.
- **Safety**: Do not assume the local directory is writable. Always use the resolved `APP_DIR` in Documents for writing data.

## Building and Running

### Running from Source
```bash
pip install -r requirements.txt
python main.py
```

### Packaging (PyInstaller)
To create a standalone `.exe`:
```bash
pyinstaller --noconfirm --onefile --windowed \
    --name "4BrosManager" \
    --icon "icon.jpg" \
    --hidden-import "PIL._tkinter_finder" \
    --collect-all "escpos" \
    --add-data "core;core" \
    --add-data "gui;gui" \
    --add-data "icon.jpg;." \
    main.py
```

## Active Technologies
- Bash / Git + None (001-cleanup-git-push)
- Local Filesystem / Git Repository (001-cleanup-git-push)

## Recent Changes
- 001-cleanup-git-push: Added Bash / Git + None
