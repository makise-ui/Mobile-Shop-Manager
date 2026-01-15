# Track Plan: Bug Fixes - Date Persistence & UI Icons

## Phase 1: Date Persistence (Search Screen)
- [x] Task: Implement `Red Phase`: Write failing tests in `tests/test_id_registry.py` ensuring `IDRegistry` stores and retrieves an 'added_date' for items, and that it preserves existing dates on update. [c6bc2e0]
- [x] Task: Implement `Green Phase`: Update `core/id_registry.py` to store `added_date` (and `sold_date`) in `metadata.json`. Update `core/inventory.py` to check this registry during import: if exists, use stored date; if new, use current date and save it. [766493f]
- [x] Task: Implement `Red Phase`: Write failing tests (or verification script) for `SearchScreen` logic to ensure it pulls dates from the persisted source/inventory correctly. [22bbfe6]
- [ ] Task: Implement `Green Phase`: Update `gui/screens.py` (Search Screen) to display the correct dates from the inventory (which now has persisted dates).
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Date Persistence (Search Screen)' (Protocol in workflow.md) [checkpoint: ]

## Phase 2: UI Icons Fix (Inventory Screen)
- [ ] Task: Diagnose asset loading. Create a script `tests/verify_assets.py` to check if `assets/icons/` files exist and are loadable by Tkinter/PIL.
- [ ] Task: Implement `Green Phase`: Fix the `_load_icons` method in `gui/screens.py` (or `gui/widgets.py` if moved) to use absolute paths or proper resource path resolution (handling both `src` and `pyinstaller` contexts).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: UI Icons Fix (Inventory Screen)' (Protocol in workflow.md) [checkpoint: ]