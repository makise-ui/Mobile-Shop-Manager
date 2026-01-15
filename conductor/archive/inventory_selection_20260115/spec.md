# Track Spec: Inventory Selection Toggle

## Overview
To improve usability in the Inventory screen, the user requested a mechanism to quickly "Check All" or "Uncheck All" items. This will be implemented as a toggle button in the toolbar.

## Functional Requirements
1.  **Toolbar Toggle:** Add a new button (or Checkbutton) in the Inventory Screen toolbar.
    *   **Label/Icon:** "☑ All" or similar.
    *   **Behavior:**
        *   If unchecked: Clicking it checks ALL items currently listed in the grid.
        *   If checked: Clicking it unchecks ALL items.
    *   **Sync:** The button state should reflect the current selection context.

2.  **Scope of Selection:**
    *   The action must apply to **visible** items in the `Treeview` (respecting current search/filters).

## Non-Functional Requirements
*   **Performance:** Selecting 1000+ items should not freeze the UI. Use efficient batch updates if possible.

## Out of Scope
*   Header-based selection (User specifically requested Toolbar).
