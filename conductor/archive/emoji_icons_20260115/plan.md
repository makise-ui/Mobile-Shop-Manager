# Track Plan: Replace Inventory Icons with Emojis

## Phase 1: Implementation (Inventory Screen)
- [x] Task: Implement `Green Phase`: Modify `InventoryScreen._load_icons` in `gui/screens.py` to remove asset loading for the toolbar buttons (Filter, Add, Print, Refresh, Search).
- [x] Task: Implement `Green Phase`: Update `InventoryScreen._init_ui` in `gui/screens.py` to use Emojis for the toolbar buttons:
    - Filter Toggle: `⚡`
    - Add to Invoice: `➕`
    - Print: `🖨️`
    - Refresh: `🔄`
- [x] Task: Implement `Green Phase`: Add/Update the search button with `🔍` emoji next to the search entry in the filter panel to ensure visibility.

## Phase 2: Verification [checkpoint: e1f0376]
- [x] Task: Conductor - User Manual Verification 'Phase 2: Verification' (Protocol in workflow.md) [checkpoint: e1f0376]
