Detailed prompt — "4 Bros Mobile" Label + Inventory Manager (Python / Tkinter)

Goal: Build a desktop app (Windows) in Python with Tkinter to manage mobile stock from Excel files, auto-watch file changes, map columns, preview & print barcode labels (thermal printer / USB), export invoices (PDF), show analytics, and calculate Indian GST (CGST+SGST). The app should be single-file/packaged later with PyInstaller.


---

High-level requirements

1. Desktop app (Windows) built with Python 3.10+ and Tkinter (native UI). Use additional libraries as needed (listed later).


2. App reads one or more Excel files (.xlsx or .csv) containing mobile stock rows and merges them into a global inventory view.


3. When a file is added, the app prompts the user to map columns (IMEI, Model, RAM, ROM, Price, Supplier, Supplier Invoice/Date, Notes, etc.). The mapping is saved for that file (JSON config).


4. The app watches added files and automatically reloads/updates inventory when the Excel file changes.


5. Dashboard shows combined stock (rows across files) with checkboxes to select items for label printing / actions.


6. Label live preview pane shows how each label will look (the small white sticker shown in second image). The label is printable to a thermal printer and exportable as a batch PDF.


7. App generates unique ID and barcode per mobile when missing; otherwise uses existing IMEI field as barcode value. Barcode uses Code128 (supports numeric + alphanumeric).


8. Manage Suppliers: user can assign a supplier globally for a file, or map a supplier column.


9. Inventory actions: mark sold, export selected items to CSV/PDF, batch-print labels, print single label, bulk-generate labels for selected items.


10. Analytics page: stock count by model, supplier, price distribution, GST reports, simple sales summary (based on marked-sold).


11. GST billing: create an invoice per sale with CGST+SGST split (user provides whether intrastate or interstate — if interstate, use IGST). Support common GST slab percentages (0, 5, 12, 18, 28). Auto-calc totals and generate PDF invoice.


12. Packaging: final deliverable should be able to compile to a Windows EXE using PyInstaller and include dependencies.




---

Libraries / tools to use

GUI: tkinter (core) + ttk for widgets

File reading: pandas (read_excel/read_csv) + openpyxl

File watching: watchdog

Barcode generation: python-barcode (Code128) or treepoem (if Image rendering required). Use Pillow to combine barcode + text for preview.

Label rendering & PDF: Pillow for raster preview, reportlab for PDF batch export.

Thermal printing / ESC/POS: python-escpos (or fallback to win32print for Windows printing).

Serial / USB: pyserial if needed.

Packaging: pyinstaller

Data persistence: tinydb or simple JSON files to store file mappings, preferences, and inventory metadata.

Optional: openpyxl for more direct Excel manipulation.



---

UI Layout (wireframe)

Top-level window with 3 vertical panes:

1. Top toolbar — buttons: Add Excel File, Manage Files, Map Columns, Scan IMEI (manual), Settings, Print, Export PDF, Analytics.


2. Left pane (Files & Filters) — list of added files; when file clicked shows mapping & supplier; filters (by model, supplier, price range, imei search).


3. Center pane (Inventory table) — DataGrid of merged rows with columns: checkbox, UniqueID, IMEI, Model, RAM, ROM, Price, Supplier, SourceFile, Status (Available/Sold), LastUpdated. Supports sorting, multi-select.


4. Right pane (Label preview + Actions) — live preview of label for currently selected row(s); label count, label size setting, Print button, Export label PDF, Batch preview scroll grid.


5. Bottom status bar — shows total items, selected count, watcher status, last sync time.



Modal dialogs:

Map Columns: when adding a file, show detected columns with sample data and provide dropdown to map to canonical fields (IMEI, Model, RAM, ROM, Price, Supplier, etc.). Save mapping per file.

Add File: browse file(s), optionally assign supplier or choose to map later.

Manage Files: show file list, mapping JSON, remove file, re-map, pause watcher, re-sync.

Settings: default label size (in mm), printer config (choose ESC/POS or Windows printer), GST defaults, default supplier, output folder, barcode format, auto-unique-id rules.



---

Label Format (exact)

Physical label: small rectangular sticker (use approximate default 50mm x 22mm) — user can calibrate label size in Settings.

Content layout (left-to-right / top-to-bottom):

4 bros mobile        (centered header)
[Barcode (Code128) centered]  <-- unique id or IMEI, barcode image (auto-generated)
Model name (aligned left)
Ram Rom (aligned left, e.g. "8GB / 128GB")
Price (aligned right, show ₹ and two decimals)

Font sizes: header small bold, barcode image dominates, model & ram medium, price bold to right.

Provide an option to show or hide supplier or other metadata.



---

Data model

Canonical fields (internal names):

unique_id (str) — auto-generated if not present. Format default 4BM-YYYYMMDD-XXXXX or simple incremental 4BM-00001.

imei (str)

model (str)

ram (str) / rom (str) or single ram_rom (str)

price (float)

supplier (str)

status (enum: Available, Reserved, Sold)

source_file (str)

row_index (int) — original row index

last_updated (datetime)

notes (str)


Store file_mappings.json:

{
  "C:\\path\\to\\file1.xlsx": {
    "mapping": {"IMEI": "imei", "MODEL": "model", "RAM_ROM": "ram_rom", "PRICE": "price"},
    "supplier": "Ramesh Electronics",
    "last_mtime": 1699999999
  }
}


---

File-watching behavior

Use watchdog to monitor added files (watch by path).

On change (modified/created), re-read file via pandas.read_excel with the saved mapping and update the internal inventory.

Detect new rows → append; detect removed rows → mark removed or deleted; detect changed rows → update fields and last_updated.

Notify user with a toast or status update: "X rows added, Y updated".



---

Column mapping rules

When mapping dialog opens, show detected headers and 3 sample rows.

Provide suggestions: if header contains imei, pre-select IMEI; if price contains ₹ or numeric values, pre-select Price.

Allow mapping to imei | unique_id | model | ram | rom | ram_rom | price | supplier | date | notes.

Allow user to choose a single supplier for the entire file instead of mapping supplier column.

Save mapping and apply automatically on subsequent re-loads.



---

Barcode & unique ID

If imei is present and is 15-digit numeric: use IMEI as barcode data.

If IMEI missing, generate unique_id. Always keep unique_id distinct and persistent for records.

Generate Code128 barcodes; create PNG via python-barcode + Pillow. Use high DPI for crisp thermal output.



---

Printing & Thermal support

Provide two printing modes:

1. Windows print: render the label as an image then send to the default Windows printer using win32print and win32ui.


2. ESC/POS: for direct thermal printers, use python-escpos to send image or ESC/POS commands. Allow configuring printer connection (USB / Serial / IP).



Allow test print. Provide a Test printer feature.

Provide batch print: generate a single PDF (with each label arranged as per label sheet) using reportlab, then either send PDF to printer or save.



---

GST & Billing

Invoice generator:

Input: selected sold items, buyer details (name, address, GSTIN if provided), invoice number (auto increment), date.

Tax calculation: for each invoice line compute taxable value = price; GST slab selected (default 18%); for intrastate split tax equally into CGST + SGST (e.g., 9% + 9%); for interstate use IGST.

Show breakdown: subtotal, taxable value, CGST amount, SGST amount, IGST amount, total.

Export invoice as PDF using reportlab with business header (store name configurable), item table, tax summary, QR code (optional).


Provide settings for default taxes and business details (store name, address, GSTIN, logo).



---

Analytics dashboard

Charts & aggregates (simple): total stock, available vs sold, top 10 models by count, stock by supplier, price histogram.

Show quick filters & export results as CSV.

Provide "GST summary" for a chosen date range: total taxable, total CGST/SGST/IGST collected.



---

Edge cases & robustness

Excel files may contain duplicates — detect by IMEI or combination (imei+model). Provide "dedupe" tools.

Non-numeric prices => ask user for correction; show preview.

If columns are renamed or file columns change, allow remapping and re-apply mapping intelligently.

Large files: pagination and lazy loading in the inventory view.

Missing barcode fonts: fallback to image barcode generation.



---

Sample Excel (example)

Columns in file (varies; user maps them):

Model, RAM, ROM, IMEI, Price, Supplier, Date
vivo V27 Pro, 8, 128, 123456789012345, 19999, Ramesh, 2026-01-02

Mapping example user chooses:

IMEI -> IMEI

Model -> Model

RAM & ROM -> Ram/ROM (app combines into "8GB / 128GB")

Price -> Price

Supplier -> Supplier



---

Acceptance criteria / Tests

1. Add a sample Excel file -> map columns -> inventory shows rows with correct fields.


2. Edit the Excel file (change price) -> app auto-detects change and updates the inventory row & last_updated.


3. Select one row -> label preview shows header, barcode (IMEI or unique id), model left, ram left, price right; print test to default printer works.


4. Batch-select 10 rows -> export labels to PDF with correct sizes and positions.


5. Create invoice for one or more items -> GST calculations correct for intrastate (CGST+SGST split) and invoice PDF generated.


6. Manage files -> re-map columns and re-sync correctly.


7. Save/Load app settings and file mappings persist across restarts.




---

Developer tasks (milestones)

1. Project skeleton + GUI main layout (Tkinter).


2. File add + mapping modal + mapping persistence.


3. Excel loader using pandas + data normalization.


4. File watcher using watchdog and sync logic.


5. Inventory table with sorting & selection.


6. Barcode generation + label rendering preview with Pillow.


7. Printing & PDF export (reportlab) + ESC/POS integration.


8. GST invoice generator + PDF export.


9. Analytics page & export.


10. Packaging with PyInstaller + user guide.




---

Sample prompt to give an LLM/developer (pasteable)

Build a Windows desktop app in Python 3.10+ using Tkinter that manages mobile inventory from Excel files, auto-watches file changes, allows per-file column mapping, previews and prints small barcode labels (Code128), supports ESC/POS thermal printing and Windows printing, and can generate GST invoices (CGST+SGST split). Use pandas, openpyxl, watchdog, Pillow, python-barcode (or treepoem), reportlab, and python-escpos. Save file mappings to JSON. Provide a user-friendly mapping dialog on file-add, a dashboard with combined inventory from all Excel files (with checkboxes and live label preview), a Manage Files panel, and an Analytics panel. Export labels as PDF and package the app with PyInstaller. Follow the label format specified: header "4 bros mobile" centered, Code128 barcode centered, model left, ram/rom left, price right. Provide sample tests and a small user guide for configuring thermal printers. Deliver code, README, and a single-file Windows EXE.


---

Extras & suggestions (nice-to-haves)

Add drag & drop for Excel files.

Add auto-scan IMEI via barcode scanner (USB) so scanning fills a field.

Provide label templates (editable) with WYSIWYG editor for power users.

Option to watermark test invoices (as in your earlier requirement).

Small settings to calibrate DPI/mm in preview for perfect label printing.

Export audit logs.

