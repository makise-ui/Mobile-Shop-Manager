# Track Plan: Inventory Selection Toggle

## Phase 1: Implementation (GUI Logic)
- [x] Task: Implement `Red Phase`: Write a test in `tests/test_widgets.py` or similar verifying selection logic (e.g., a function that checks all items in a mock list). [1e7d354]
- [x] Task: Implement `Green Phase`: Add `_select_all()` and `_deselect_all()` methods to `InventoryScreen` in `gui/screens.py`. [0e34595]
- [x] Task: Implement `Green Phase`: Add the "Check All" toggle button to the Inventory toolbar in `gui/screens.py`. [0e34595]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Implementation' (Protocol in workflow.md) [checkpoint: 0e34595]

## Phase 2: Refinement & UX [checkpoint: 0e34595]
- [x] Task: Ensure the toggle respects the current filtered view. [Verified by Code Review]
- [x] Task: Add keyboard shortcut `Ctrl+A` for Select All and `Ctrl+Shift+A` for Deselect All. [Verified Existing]
- [x] Task: Conductor - User Manual Verification 'Phase 2: Refinement' (Protocol in workflow.md) [checkpoint: 0e34595]
