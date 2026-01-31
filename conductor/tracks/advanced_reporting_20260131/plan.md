# Implementation Plan - Advanced Reporting & Custom Extraction

## Phase 1: Core Logic & Backend [checkpoint: 411197b]
- [x] Task: Extend `ReportGenerator` in `core/reporting.py` [411197b]
    - [x] Add support for "Modulo" operator in `apply_conditions`.
    - [x] Implement `apply_limit(df, limit)` function.
    - [x] Implement `apply_custom_expression(df, expression_str)` using pandas `query()`.
- [x] Task: Write Tests for New Logic [411197b]
    - [x] Create `tests/test_advanced_reporting.py`.
    - [x] Test Modulo filtering.
    - [x] Test Date range/boundary logic.
    - [x] Test Custom Expression parsing and safety.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Core Logic & Backend' (Protocol in workflow.md) [411197b]

## Phase 2: UI Components (Widgets) [checkpoint: 67e7996]
- [x] Task: Create `AdvancedFilterPanel` Widget [67e7996]
    - [x] Refactor existing filter row logic into `gui/widgets.py` or `gui/screens/reporting.py`.
    - [x] Integrate `ttkbootstrap.DateEntry` for date fields.
    - [x] Add "Relative Date" dropdown logic.
- [x] Task: Create `SamplingPanel` Widget [67e7996]
    - [x] Create UI for "Row Limit" (Spinbox).
    - [x] Create UI for "Modulo" (Field selector + Divisor + Remainder).
    - [x] Create UI for "Custom Expression" (Text Area).
- [x] Task: Conductor - User Manual Verification 'Phase 2: UI Components (Widgets)' (Protocol in workflow.md) [67e7996]

## Phase 3: Screen Integration & Preview Flow [checkpoint: 7203b16]
- [x] Task: Refactor `ReportingScreen` Layout [7203b16]
    - [x] Split screen into "Config View" and "Preview View".
    - [x] Integrate `AdvancedFilterPanel` and `SamplingPanel` into "Config View".
- [x] Task: Implement Preview Logic [7203b16]
    - [x] Add "Preview Data" button.
    - [x] Implement state switching (Config <-> Preview).
    - [x] Render `pd.DataFrame` result into a temporary Treeview in "Preview View".
- [x] Task: Conductor - User Manual Verification 'Phase 3: Screen Integration & Preview Flow' (Protocol in workflow.md) [7203b16]

## Phase 4: Final Polish & Export
- [ ] Task: Connect Export Functionality
    - [ ] Ensure "Export" button on Preview screen uses the filtered data.
- [ ] Task: Validation & UX
    - [ ] Add tooltips for Custom Expressions (examples).
    - [ ] Validate numeric inputs for Modulo/Limit.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Polish & Export' (Protocol in workflow.md)
