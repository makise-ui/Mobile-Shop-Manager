# Specification: Advanced Reporting & Custom Extraction

## Overview
Enhance the existing "Advanced Reporting" screen to provide users with "Full Control" over data extraction. This includes advanced date filtering, mathematical sampling (modulo), row limits, and a preview system to verify data before final export.

## Functional Requirements

### 1. Enhanced Date Filtering
- **DatePicker Integration:** When the "Date" field (or `last_updated`) is selected in a filter row, provide a calendar widget instead of a plain text entry.
- **Relative Date Presets:** Support operators/values like "Last 7 Days", "Last 30 Days", and "This Month".
- **Boundary Support:** Explicit support for "Above" (Greater Than) and "Below" (Less Than) specific dates.

### 2. Custom Extraction Logic
- **Advanced Sidebar:** A dedicated UI panel for "Sampling & Limits".
- **Mathematical Sampling (Modulo):** Ability to filter rows based on a modulo operation (e.g., `ID % 2 == 0` for even IDs).
- **Row Limits:** Ability to cap the extraction to a specific number of rows (e.g., "First 100 items").
- **Manual Expression Override:** A text area for advanced users to write complex logical queries directly (e.g., `supplier == 'AB' and id % 2 == 0`).

### 3. Verification & Preview
- **Preview Button:** A button that generates the report in memory.
- **UI Transition:** When clicked, the configuration panel is replaced by a temporary Data Table (Treeview) showing the filtered results.
- **Navigation:** A "Back" button on the preview screen to return to the filter configuration.

## Non-Functional Requirements
- **Responsiveness:** Preview generation should be efficient, utilizing the background loading patterns established in the inventory screen.
- **Consistency:** Maintain the `ttkbootstrap` styling.

## Acceptance Criteria
- User can successfully extract only items with even-numbered IDs up to a certain limit.
- User can filter by a date range using a calendar widget.
- User can preview data and see exactly what will be exported before saving the file.
- The manual expression box correctly overrides or appends to the UI conditions.

## Out of Scope
- Real-time chart visualization within the preview (table only).
- Multi-file merging during extraction (logic stays within current loaded inventory).
