# Technology Stack: Mobile Shop Manager

## 1. Core Language & Runtime
*   **Python 3.10+**: Chosen for its robust data processing libraries and rapid GUI development capabilities.
*   **PyInstaller**: Used to package the Python application into a standalone Windows executable (.exe).

## 2. User Interface (GUI)
*   **Tkinter**: The standard Python interface to the Tk GUI toolkit.
*   **ttkbootstrap**: Provides modern, flat-design themes and widgets for Tkinter, improving the visual appeal and UX.

## 3. Data Management & Processing
*   **Pandas**: High-performance data structures and data analysis tools for managing inventory tables.
*   **OpenPyXL**: A Python library to read/write Excel 2010 xlsx/xlsm/xltx/xltm files.
*   **TinyDB / JSON**: Lightweight, document-oriented database and JSON files for persistent configuration and metadata storage.

## 4. Hardware & OS Integration
*   **PyWin32 (Win32 API)**: Critical for direct interaction with Windows spooler and thermal printers (ZPL).
*   **Watchdog**: Cross-platform API and shell utilities to monitor file system events (Excel sync).

## 5. Document & Asset Generation
*   **ReportLab**: Engine for generating professional PDF invoices and reports.
*   **python-barcode**: Generation of Code128 barcodes for retail labels.
*   **Pillow (PIL)**: Image processing for icons and logos.

## 6. Security & Licensing
*   **pycryptodome**: Cryptographic primitives for hardware-locked licensing and data protection.
