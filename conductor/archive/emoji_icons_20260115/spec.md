# Track Spec: Replace Inventory Icons with Emojis

## Overview
The icons in the Inventory screen (Filter, Add, Print, etc.) have been problematic with loading/visibility. The user has requested to replace these image-based assets with standard Unicode Emojis. This will simplify the codebase, remove external asset dependencies for these controls, and ensure visibility across different themes/modes.

## Functional Requirements
1.  **Replace Icons:** The following actions in the Inventory Screen must use Emojis instead of Image assets:
    *   **Filter Toggle:** ⚡
    *   **Add to Invoice:** ➕
    *   **Print:** 🖨️
    *   **Refresh:** 🔄
    *   **Search:** 🔍 (Ensure visible in Filter Panel)

2.  **Code Cleanup:**
    *   Remove the `_load_icons` logic that attempts to load `plus-lg.png`, `printer.png`, etc., for these specific buttons from `InventoryScreen`.
    *   Update `InventoryScreen._init_ui` to instantiate `IconButton` (or `ttk.Button`) with `text` instead of `image`.

## Non-Functional Requirements
*   **Maintainability:** Reduces dependency on `assets/` folder for core UI.
*   **Performance:** Slightly faster load time (no disk I/O for icons).

## Out of Scope
*   Replacing app window icon (`.ico`).
*   Replacing splash screen image.
