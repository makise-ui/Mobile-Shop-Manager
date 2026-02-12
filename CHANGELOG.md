# Changelog

## [v1.10.0] - 2026-02-12: The Reporting & Help Update

### 🚀 Major Features
*   **Context-Aware Help System:** Added a **"❓ Help"** button to every screen header. Clicking it instantly opens the relevant section of the User Guide (e.g., Inventory Help, Billing Guide).
*   **Manual Scan Reporting:** A dedicated module for high-speed barcode scanning sessions with live metrics, persistent sessions, and direct Excel/PDF export.
*   **Advanced Reporting 2.0:**
    *   **Dynamic Filters:** Dropdowns now populate with *real data* from your inventory (e.g., existing Brands/Suppliers).
    *   **Logic Gates:** Added powerful `AND`, `OR`, `XOR`, `AND NOT` operators for complex queries.
    *   **Presets:** Included built-in examples (e.g., "High-Value Stock", "Sales Last Week") to help you get started quickly.
    *   **Persistence:** Your complex filters are now saved automatically between sessions.

### 🛠 Enhancements
*   **Duplicate IMEI Protection:** Quick Entry now warns you *immediately* (in the status bar) if an IMEI exists. It also enforces a hard stop confirmation before saving a duplicate.
*   **Adjustable UI:** The Reporting screen now features a resizable split-pane layout for better usability on different screen sizes.
*   **Markdown Engine:** Refactored the internal help viewer for better text wrapping, spacing, and stability.

### 🐛 Fixes
*   **ZPL Designer:** Fixed threading issues with preview generation.
*   **Navigation:** Improved keyboard traversal in Quick Entry and Status screens.

## [v1.8.1] - 2026-01-15: Critical Stability Patch

### 🛠 Fixes
*   **Crash Fix:** Resolved a crash in the Inventory Screen ("Select All" toggle) caused by a missing method reference. The "Check/Uncheck All" feature now functions correctly.

## [v1.8.0] - 2026-01-15: The Stability & Icon Update

### 🎨 Visual & UI Enhancements
*   **Emoji Icons:** Replaced missing image-based icons in the Inventory toolbar (Filter, Add, Print, Refresh, Search) with standard Unicode emojis (⚡, ➕, 🖨️, 🔄, 🔍). This ensures controls are always visible regardless of theme or missing assets.
*   **Consistent Styling:** Unified button styles in the Inventory screen for a cleaner look.

### 🛡️ Core Stability & Fixes
*   **Conflict Suppression:** The "Conflict Detected" popup is now suppressed in the **Quick Status** screen (in addition to Quick Entry), preventing interruptions during high-speed status updates (IN/OUT/RTN).
*   **Crash Fix:** Resolved a critical crash (`AttributeError`) in the Status Screen when confirming an update, related to incorrect method calls on autocomplete fields.
*   **Date Persistence:** Fixed a bug where "Date Added" and "Date Sold" would reset to the current date on every reload. The app now persistently tracks the original import date for each item using its internal registry.
*   **Startup Fix:** Fixed a `NameError: name 'sys' is not defined` crash that could occur on certain platforms/environments during startup.

## [v1.7.0] - 2026-01-12: The "Sequential Entry" Update

### 🚀 Batch & Sequential Entry
*   **Batch Scan Queue:** A new "Batch Mode" in Quick Entry allows you to scan a queue of IMEIs first (e.g., scanning 50 phones in a row) and then process them one by one.
*   **Sequential Workflow:** When saving an entry in Batch Mode, the form automatically loads the next IMEI from your queue, keeping your hands on the keyboard for maximum speed.
*   **Queue Management:** You can now see a log of scanned items and remove accidental scans via the **Delete** key or **Right-Click** menu before processing.

### 🧠 Smart Navigation & Autocomplete
*   **Intelligent Auto-Focus:** Pressing `Enter` now automatically **skips locked fields**. If you lock "Supplier" and "Grade", the cursor jumps straight from Price to Condition, saving keystrokes.
*   **Full Keyboard Control:** Added `Up/Down` arrow key navigation to move between fields freely, even if they are locked.
*   **Autocomplete Everywhere:** Replaced standard text boxes with **Smart Autocomplete** for:
    *   **Model Name** (Learns from your inventory)
    *   **RAM/ROM & Specs**
    *   **Suppliers**
    *   **Conditions** (New!)
    *   **Grades**

### 🛠 Core & UX Improvements
*   **Conditions Registry:** Added backend support for tracking item "Conditions" (e.g., "Mobile Only", "Full Kit").
*   **Flexible ID Entry:** Batch Mode now accepts non-numeric IDs (like "DISPLAY OUT" or alphanumeric codes) without forcing you to toggle "Manual Mode".
*   **Conflict Suppression:** The "Conflict Detected" popup is now **suppressed** specifically while using the Quick Entry screen, preventing workflow interruptions during high-speed data entry.
*   **Blank Screen Fix:** Resolved an issue where the Quick Entry screen would sometimes appear blank on initial load.

---

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