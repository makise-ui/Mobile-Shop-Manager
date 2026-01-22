# Track Plan: Fix File Selection Visibility in Quick Entry

## Phase 1: Implementation
- [x] Task: Implement `Red Phase`: Write a test in `tests/test_logic.py` or a new test file verifying that path-to-basename conversion logic works correctly and handles potential duplicates. [3a6c534]
- [ ] Task: Implement `Green Phase`: Update `QuickEntryScreen` in `gui/quick_entry.py` to use a display map for file selection.
    - [ ] Create `self.file_display_map` in `__init__`.
    - [ ] Modify `_refresh_files` to populate values with basenames.
    - [ ] Update `_save_entry` and other methods to resolve full paths from display names.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Implementation' (Protocol in workflow.md) [checkpoint: ]

## Phase 2: Refinement
- [ ] Task: Increase `combo_file` width slightly in `_init_ui` for better visibility of long filenames.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Refinement' (Protocol in workflow.md) [checkpoint: ]
