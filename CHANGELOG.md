# Changelog

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
