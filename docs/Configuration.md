# Configuration Guide

All configuration files are stored in `Documents\4BrosManager\config\`.

## 1. Application Settings (`config.json`)

You can edit these settings via the **Settings** screen in the app, or manually edit the JSON file.

| Key | Description | Default |
| :--- | :--- | :--- |
| `store_name` | Name printed on labels and invoices. | "4bros Mobile Point" |
| `store_address` | Address for the invoice header. | ... |
| `printer_type` | `windows` (Standard) or `zpl` (Raw commands). | `windows` |
| `label_width_mm` | Width of a *single* label. | 50 |
| `label_height_mm` | Height of a *single* label. | 22 |
| `price_markup_percent` | % added to Purchase Price to set Selling Price. | 0.0 |
| `gst_default_percent` | GST rate used for tax calculations. | 18.0 |

## 2. File Mappings (`file_mappings.json`)

This file stores how your Excel columns map to the application.

**Example Structure:**
```json
{
  "C:/Users/Admin/Desktop/Stock.xlsx": {
    "sheet_name": "Sheet1",
    "mapping": {
      "Mobile Name": "model",
      "IMEI Number": "imei",
      "Cost": "price",
      "Colour": "color"
    }
  }
}
```

*   **`model`**: The internal name for the product model.
*   **`imei`**: The unique serial number.
*   **`price`**: The buying price (Cost).
*   **`color`**: The product color.

## 3. ID Registry (`id_registry.json`)

**CRITICAL FILE**. Do not edit manually unless you know what you are doing.

This file links the item's `IMEI` + `Model` to a generated `Unique ID` (e.g., "4BM001"). It also stores the status (`IN`/`OUT`).

If you delete this file:
1.  All your items will be assigned NEW Unique IDs.
2.  All "Sold" statuses will be lost (items will reappear as IN).

