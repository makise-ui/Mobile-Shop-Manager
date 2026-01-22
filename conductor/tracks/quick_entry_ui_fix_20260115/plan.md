# Track Plan: Fix File Selection Visibility in Quick Entry

## Phase 1: Implementation
- [x] Task: Implement `Red Phase`: Write a test in `tests/test_logic.py` or a new test file verifying that path-to-basename conversion logic works correctly and handles potential duplicates. [3a6c534]
- [x] Task: Implement `Green Phase`: Update `QuickEntryScreen` in `gui/quick_entry.py` to use a display map for file selection. [d6573a5]
    - [x] Create `self.file_display_map` in `__init__`. [d6573a5]
    - [x] Modify `_refresh_files` to populate values with basenames. [d6573a5]
    - [x] Update `_save_entry` and other methods to resolve full paths from display names. [d6573a5]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Implementation' (Protocol in workflow.md) [checkpoint: d6573a5]

## Phase 2: Refinement
- [ ] Task: Increase `combo_file` width slightly in `_init_ui` for better visibility of long filenames.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Refinement' (Protocol in workflow.md) [checkpoint: ]
