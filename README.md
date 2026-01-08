# Mobile Shop Manager

A specialized enterprise solution for mobile retail inventory management, GST billing, and precision thermal printing.

![Version](https://img.shields.io/github/v/release/makise-ui/Mobile-Shop-Manager?style=flat-square&color=007acc) ![Platform](https://img.shields.io/badge/Platform-Windows-007acc?style=flat-square) ![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)

---

## Overview

**Mobile Shop Manager** eliminates the complexity of tracking serialized inventory (IMEI) across multiple storage locations. Unlike generic POS systems, it is engineered specifically for the mobile device retail sector, featuring native integration with Excel-based workflows and industrial thermal printers.

Key differentiator: **Zero-Data-Entry Sync**. The system watches your existing Excel stock sheets and updates the inventory in real-time, requiring no manual import/export cycles.

## Core Capabilities

### Inventory & Stock
*   **Real-time Excel Synchronization:** Automatically detects and merges changes from multiple `.xlsx` sources.
*   **Serialized Tracking:** Unique ID assignment for every unit, tracking movement from "In Stock" to "Sold" or "Returned" seamlessly.
*   **Conflict Resolution:** Intelligent detection of duplicate IMEIs across different supplier files.

### Point of Sale & Billing
*   **GST Invoicing:** Compliant tax generation (CGST/SGST/IGST) with automated state code detection.
*   **Buyer Management:** integrated customer database to auto-fill details for recurring clients.
*   **Sales Analytics:** Daily revenue reports, profit margin analysis, and stock aging alerts.

### Precision Labeling
*   **Native ZPL Engine:** Direct hardware control for Zebra/TSC thermal printers.
*   **2-Up Printing:** Specialized support for printing two different product labels side-by-side on a single row, optimizing media usage.
*   **Visual Designer:** Built-in drag-and-drop template designer for creating custom sticker layouts.

---

## Installation

### For End Users
1.  Download the latest installer (`.exe`) from the **Releases** section.
2.  Run the application.
3.  On first launch, you will be prompted to activate your license.
4.  Enter your Store Name and details to configure the billing engine.

### For Developers
**Prerequisites:** Python 3.10+, Windows 10/11.

```bash
# Clone the repository
git clone https://github.com/makise-ui/Mobile-Shop-Manager.git

# Install dependencies
pip install -r requirements.txt

# Run from source
python main.py
```

---

## Architecture

The application is built on a robust Python stack designed for reliability and ease of deployment.

*   **GUI Framework:** Tkinter with `ttkbootstrap` for a modern, responsive interface.
*   **Data Engine:** `pandas` for high-performance Excel processing and `TinyDB` for lightweight state persistence.
*   **Printing Subsystem:** Raw Win32 API integration (`win32print`) for direct ZPL command transmission to thermal printers.
*   **Security:** Hardware-locked licensing system using local hardware identifiers.

---

## Configuration

User data is strictly separated from the application logic to ensure seamless updates.

*   **Config Location:** `Documents/MobileShopManager/config/`
*   **Database:** `Documents/MobileShopManager/id_registry.json`
*   **Templates:** `Documents/MobileShopManager/config/templates/`

---

## License & Support

**Proprietary Software.**
Copyright (c) 2026 Makise UI / 4 Bros Mobile. All rights reserved.

Unauthorized reproduction, distribution, or reverse engineering of this software is strictly prohibited.

**Support Contact:**
For enterprise licensing, AMC contracts, or technical support, please contact the development team directly.