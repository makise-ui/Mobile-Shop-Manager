# Track Spec: Bug Fixes - Date Persistence & UI Icons

## Overview
This track addresses two critical bugs:
1.  **Date Persistence:** Items in the Search Screen (and potentially elsewhere) show the current date for "Item In" and "Date Sold" because the source Excel files lack date columns, and the app is likely failing to persist the initial import/sale timestamp, defaulting to "today" on every reload.
2.  **Invisible Icons:** The newly added action icons (Filter, Add to Invoice, Print) in the Inventory Screen are invisible (blank space) but clickable, likely due to an asset path or rendering issue.

## Functional Requirements
1.  **Date Persistence:**
    *   **Import Date:** When an item is first imported from Excel, record the timestamp (Date Added).
    *   **Persistence:** This 'Date Added' must be stored persistently (e.g., in `id_registry.json` or a dedicated metadata store) so that subsequent reloads (even if Excel is untouched) retain the original date, not "today's date".
    *   **Search Screen:** Display the correct historical 'Date Added' and 'Date Sold' in the Search Screen.
    *   **Fallback:** If an item has no recorded date, it can default to "Unknown" or the first-seen date, but must stop updating to "Current Date" on every view.

2.  **UI Assets (Inventory Screen):**
    *   **Icons:** Ensure the 'Filter', 'Add to Invoice', and 'Print' icons are visible in the Inventory Screen toolbar.
    *   **Asset Loading:** Verify `assets/icons/` paths are correctly resolved at runtime (both source and potentially frozen, though source is priority).

## Non-Functional Requirements
*   **Data Integrity:** Existing inventory IDs should attempt to recover or stabilize their dates if possible (or start tracking correctly from now on).
*   **Performance:** Icon loading should not slow down screen initialization.

## Out of Scope
*   Adding date columns to the user's Excel files (we fix it in the App's internal storage).
*   Changes to the "Billing" screen logic (unless directly related to Sold Date persistence).