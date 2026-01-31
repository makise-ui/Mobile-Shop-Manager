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

## Phase 2: UI Components (Widgets)
- [ ] Task: Create `AdvancedFilterPanel` Widget
    - [ ] Refactor existing filter row logic into `gui/widgets.py` or `gui/screens/reporting.py`.
    - [ ] Integrate `ttkbootstrap.DateEntry` for date fields.
    - [ ] Add "Relative Date" dropdown logic.
- [ ] Task: Create `SamplingPanel` Widget
    - [ ] Create UI for "Row Limit" (Spinbox).
    - [ ] Create UI for "Modulo" (Field selector + Divisor + Remainder).
    - [ ] Create UI for "Custom Expression" (Text Area).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: UI Components (Widgets)' (Protocol in workflow.md)

## Phase 3: Screen Integration & Preview Flow
- [ ] Task: Refactor `ReportingScreen` Layout
    - [ ] Split screen into "Config View" and "Preview View".
    - [ ] Integrate `AdvancedFilterPanel` and `SamplingPanel` into "Config View".
- [ ] Task: Implement Preview Logic
    - [ ] Add "Preview Data" button.
    - [ ] Implement state switching (Config <-> Preview).
    - [ ] Render `pd.DataFrame` result into a temporary Treeview in "Preview View".
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Screen Integration & Preview Flow' (Protocol in workflow.md)

## Phase 4: Final Polish & Export
- [ ] Task: Connect Export Functionality
    - [ ] Ensure "Export" button on Preview screen uses the filtered data.
- [ ] Task: Validation & UX
    - [ ] Add tooltips for Custom Expressions (examples).
    - [ ] Validate numeric inputs for Modulo/Limit.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Polish & Export' (Protocol in workflow.md)
