# Track Spec: Fix File Selection Visibility in Quick Entry

## Overview
The file selection dropdown in the Quick Entry screen currently displays full absolute file paths. Due to the limited width of the dropdown, the actual filename (which is usually at the end of the path) is often hidden or cut off, making it difficult for users to select the correct file.

## Functional Requirements
1.  **Shorten Display Names:** The dropdown menu (`combo_file`) in the Quick Entry screen must show only the base filename (e.g., `inventory.xlsx`) instead of the full path.
2.  **Internal Path Mapping:** The application must maintain a mapping between the displayed filename and the underlying full path so that saving operations continue to target the correct location.
3.  **UI Width:** Ensure the dropdown has a reasonable width to display most filenames comfortably.

## Implementation Details
*   **Location:** `gui/quick_entry.py`
*   **Logic:**
    *   In `_refresh_files`, instead of populating `self.combo_file['values']` directly with path keys, transform them using `os.path.basename`.
    *   Store a lookup dictionary `self.file_display_map = {basename: fullpath}`.
    *   Update methods to resolve the full path from the selected basename.

## Non-Functional Requirements
*   **Reliability:** Ensure unique display names even if filenames are identical in different folders (e.g. by appending parent folder if needed).

## Out of Scope
*   Redesigning the entire settings/mappings system.
