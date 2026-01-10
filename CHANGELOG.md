# Changelog

## [v1.6.0] - 2026-01-10: Architecture & Multi-Select Update

### ⚡ Performance & Core
*   **Background Writes:** Inventory updates (Excel saving) now happen in a background thread, preventing the UI from freezing during large save operations.
*   **Auto-Backup Rotation:** The system now automatically rotates backups of your Excel files, keeping only the last 5 safe copies to save disk space while ensuring data safety.
*   **Cross-Platform Core:** Enhanced core libraries (Barcode, Printer) to be robust on Linux/macOS for safer development, with better fallback fonts.
*   **Constants Refactor:** Internal logic moved to a centralized `constants.py` to improve stability and reduce bugs.

### 🎮 Inventory UI Overhaul
*   **Multi-Select:** Added powerful keyboard shortcuts for selecting multiple items in the Inventory grid:
    *   `Ctrl + Shift + Arrow Up/Down`: Check items sequentially.
    *   `Ctrl + Shift + Home/End`: Check all items from current to start/end.
    *   `Ctrl + A`: Select All.
*   **Selection Stats:** Added a live "Total Stocks | Selected" counter to the Inventory screen for better visibility.
*   **Range Tracking:** Smart tracking of the "Anchor" item allows for intuitive range selection.

### 🛡️ Security
*   **Input Sanitization:** Fixed potential command injection vulnerabilities in the licensing module.
*   **Resource Safety:** Improved printer handle management to prevent resource leaks and crashes on Windows.

---

## [v1.5.0] - 2026-01-10: AI & Simulation Update

### 🧠 Intelligence & Analytics
*   **Price Simulation Mode:** Added a powerful "What-If" engine to Analytics and Dashboard. You can now visualize costs and profits based on hypothetical scenarios (e.g., "Assume Original Cost is Selling Price - 8%") without altering your real database.
*   **AI Demand Forecasting:** New "AI Insights" widget on the Dashboard predicts stockouts based on your sales velocity. It alerts you to "Low Stock" or "Dead Stock" items automatically.
*   **Smart Settings:** Added a dedicated "Intelligence" tab in Settings to toggle AI features on/off.

### 🚀 Enhancements
*   **Dashboard Upgrade:** Added a settings shortcut directly to the Dashboard header for quick access to simulation tools.
*   **Visual Indicators:** Clear warnings ("⚠️ SIMULATION ACTIVE") appear when viewing hypothetical data to prevent confusion with real financial records.

---

## [v1.4.0] - 2026-01-09: The Reporting & Analytics Update

### 🚀 New Features

#### Advanced Reporting Suite
*   **Custom Query Builder:** Create complex "If/Else" style filters (e.g., "Status is IN AND Price > 10,000") to target specific inventory segments.
*   **Flexible Exports:** Added support for exporting reports to **Microsoft Word (.docx)**, **Excel (.xlsx)**, and **PDF**.
*   **Column Customization:** New "Dual Listbox" interface allows you to choose exactly which fields to export and **reorder** them (Drag & Drop / Up & Down).
*   **Presets:** Save time with built-in presets for common queries like "Low Stock", "Expensive Items", and "Returns".
*   **Serial Numbering:** Option to inject an "S.No" column into exports for easy row counting.

#### Enhanced Analytics Dashboard
*   **Detailed PDF Report:** The Analytics export has been completely rewritten. It now generates a professional multi-page PDF containing:
    *   **Financial Snapshot:** Total value, items sold, and realized profit.
    *   **Detailed Sales Log:** A full history table of sold items including Date, Buyer Name, Model, and Sale Price.
*   **Brand Extraction:** The system now automatically extracts the "Brand" from the Model name (e.g., "Apple iPhone 13" -> "APPLE") if a dedicated Brand column is missing, enabling better charts and reporting.

#### Inventory & Pricing Logic
*   **Smart Price Rounding:** The "Price Markup" feature now automatically rounds the calculated selling price to the nearest **100** (e.g., 4540 -> 4500, 4560 -> 4600) for cleaner retail pricing.
*   **Brand Column Support:** The inventory engine now natively supports a 'Brand' column if provided in the source Excel file.

### 🛠 Improvements & Fixes
*   **Search Screen:** Fixed a layout bug where the details pane would duplicate itself on repeated searches.
*   **Shortcuts:** Improved reliability of global hotkeys (F1-F5) and navigation shortcuts (Ctrl+N).
*   **Help System:** Updated the in-app User Guide to reflect the new Reporting and Analytics capabilities.
*   **Logs:** Removed excessive navigation logging to keep the console clean.

---

## [v1.3.0] - 2026-01-09: The Productivity Update

### 🚀 New Features
*   **Global Hotkeys:** Added F1-F5 shortcuts for rapid navigation (Search, Quick Entry, Status, Billing, Refresh).
*   **Inline Autocomplete:** Replaced standard dropdowns with Excel-style "Type-Ahead" input fields for faster data entry in Search, Status, and Billing screens.
*   **Context Menus:** Right-click context menus added to inventory grids for quick actions.
*   **Dashboard Analytics:** Added "Top Sellers" and improved financial summaries on the main dashboard.

### 🛠 Fixes
*   **Focus Management:** Resolved crashes related to input focus when switching screens.
*   **Stability:** General stability improvements and shortcut conflict resolution.

---

## [v1.2.0] - 2026-01-07

### 🚀 New Features

#### Visual ZPL Designer Overhaul
*   **2-Up Label Support:** The designer now defaults to a "Wide" mode (830 dots) to support designing two labels side-by-side (Left & Right) for standard 2-up thermal rolls.
*   **Template Management system:**
    *   **Save/Load:** You can now save your designs as `.zpl` files in a dedicated `config/templates/` directory.
    *   **Set as Active:** A new button allows you to instantly apply your current design as the global print template for the Inventory "Print Labels" function.
    *   **Test Print:** Added a button to print the current design directly to the default printer with dummy data, allowing for quick alignment checks.
*   **Enhanced Design Tools:**
    *   **Text Alignment:** Added support for **Left**, **Center**, and **Right** text alignment using ZPL Field Blocks (`^FB`).
    *   **Conditional Logic:** The "Grade" box now uses intelligent ZPL (`^FR` + Inverted Text) so that it completely disappears if the item has no grade, preventing empty black boxes.
    *   **Batch Variables:** Added support for `_2` suffix variables (e.g., `${model_2}`, `${price_2}`) to correctly populate the right-side label in batch printing jobs.

#### UI/UX Improvements
*   **Scrollable Preview:** The Live Preview pane is now full-width and scrollable, ensuring you can inspect the entire 2-up label layout.
*   **Layout Redesign:** Moved the ZPL Code editor to the right sidebar to maximize screen space for the design canvas and preview.
*   **Safety Checks:** Added confirmation dialogs when overwriting the active print template.

### 🛠 Tech & Core Updates
*   **Core Printer Logic:** Updated `print_batch_zpl` in `core/printer.py` to check for and load `custom_template.zpl`. It falls back to the legacy hardcoded format only if no custom template is active.
*   **Direct Printing:** Added `send_raw_zpl` method to `PrinterManager` for bypassing the template engine when testing designs.
*   **Stability:** Fixed crash in ZPL Designer due to incorrect context passing (`AttributeError`).

---

## [v1.1.5]
*   Initial stable release with basic Inventory and Billing features.