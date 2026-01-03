# Troubleshooting

## Printer Issues

### 1. Labels are misaligned or printing blank
*   **Cause**: Incorrect Page Size in Windows Printer Settings.
*   **Fix**:
    1. Go to Windows **Printers & Scanners**.
    2. Select your thermal printer -> **Manage** -> **Printing Preferences**.
    3. Under **Page Setup**, ensure the size matches your physical label roll.
    4. *Note for 2-up labels*: If you have two 50mm labels side-by-side, the "Page Width" is usually 100mm (plus margins), not 50mm.

### 2. "ZPL Print Error"
*   **Cause**: The printer driver is not accepting raw commands or the printer name is wrong.
*   **Fix**:
    *   Ensure the printer is set as the **Default Printer** in Windows.
    *   Try switching `printer_type` to `windows` in Settings if your printer doesn't support ZPL.

### 3. Text is cut off on the label
*   **Cause**: The label size in the app doesn't match the ZPL template.
*   **Fix**: The ZPL code in `core/printer.py` is hardcoded for specific dimensions (approx 50x25mm). If your labels are smaller, you may need to adjust the coordinates in the python code.

## Excel / Data Issues

### 1. "Mapping Required" Error
*   **Cause**: You added a file but didn't finish mapping the columns.
*   **Fix**: Go to **Settings -> Manage Files**, select the file, and click **Edit Mapping**. Ensure all required fields (Model, IMEI) are mapped.

### 2. Changes in Excel are not showing
*   **Cause**: The app only reads the file when it is *saved*.
*   **Fix**: Save your Excel file (Ctrl+S). The app should refresh automatically. If not, click the **Refresh** button on the dashboard.

### 3. Duplicate IDs or "Conflict"
*   **Cause**: The same IMEI appears in two different files, or twice in the same file.
*   **Fix**: The app should show a "Conflict Resolution" dialog. You can choose to "Merge" (keep one entry) or "Ignore". Check your source Excel files for duplicates.
