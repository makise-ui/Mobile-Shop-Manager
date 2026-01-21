# Mobile Shop Manager

An open-source Windows desktop application for mobile shop inventory management, featuring Excel sync, GST billing, and ZPL thermal printing.

## Key Features

*   **Excel Sync:** Automatically merges inventory from multiple Excel files.
*   **Inventory Tracking:** Persistent status (Sold/Returned) for unique items (IMEI).
*   **GST Billing:** Generates PDF invoices with tax calculations.
*   **Thermal Printing:** Native ZPL support for high-speed, 2-up label printing.
*   **Analytics:** Dashboard for stock value, profit, and sales history.

## Installation & Running

### For Users
1.  Download the latest release from the [Releases](https://github.com/hasanfq6/Mobile-Shop-Manager/releases) page.
2.  Run the `.exe` file.
3.  On first launch, enter your Store Details and map your Inventory Excel file.

### For Developers

**Prerequisites:** Python 3.10+, Windows 10/11.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hasanfq6/Mobile-Shop-Manager.git
    cd Mobile-Shop-Manager
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    python main.py
    ```

4.  **Build executable (optional):**
    ```bash
    pip install pyinstaller
    pyinstaller --noconfirm --onefile --windowed --name "4BrosManager" --hidden-import "PIL._tkinter_finder" --collect-all "escpos" --add-data "core;core" --add-data "gui;gui" main.py
    ```

## Project Structure

*   `main.py`: Entry point.
*   `core/`: Backend logic (Inventory, Printer, Billing, Config).
*   `gui/`: UI components (Screens, Dialogs).
*   `config/`: User data storage (JSON files).

## Data Storage
User data (config, logs, backups) is stored in your Documents folder: `Documents/MobileShopManager/`.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
Email: hasanfq818@gmail.com