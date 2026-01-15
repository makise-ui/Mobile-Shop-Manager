# Track Plan: Inventory UI Overhaul - Advanced Filters & Compact Icons

## Phase 1: Icon Infrastructure & Toolbar Refactor [checkpoint: 81898f7]
- [x] Task: Create or source a set of Bootstrap-style icons (PNG/ICO) for Add, Print, Delete, Refresh, Filter, Search. [a8e20e3]
- [x] Task: Implement `Green Phase`: Create a reusable `IconButton` component in `gui/widgets.py` (or equivalent) that supports tooltips. [c3863e8]
- [x] Task: Refactor `gui/screens.py` (Inventory Screen) to replace the top button bar with a compact toolbar using the new `IconButton`. [81898f7]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Icon Infrastructure & Toolbar Refactor' (Protocol in workflow.md) [checkpoint: 81898f7]

## Phase 2: Advanced Filter Logic [checkpoint: 2b45cdb]
- [x] Task: Implement `Red Phase`: Write failing tests for a new `AdvancedFilter` class that filters the inventory DataFrame based on complex criteria (Date ranges, Supplier list). [26dd47a]
- [x] Task: Implement `Green Phase`: Implement the `AdvancedFilter` logic in `core/inventory.py` (or `core/filters.py`). [2b45cdb]
- [x] Task: Conductor - User Manual Verification 'Phase 2: Advanced Filter Logic' (Protocol in workflow.md) [checkpoint: 2b45cdb]

## Phase 3: Filter UI Implementation
- [x] Task: Create a `CollapsiblePanel` widget in `gui/widgets.py`. [ad2591b]
- [ ] Task: Implement the "Advanced Filter" form inside the collapsible panel on the Inventory screen.
- [ ] Task: Wire up the UI inputs (Date pickers, Dropdowns) to the `AdvancedFilter` logic.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Filter UI Implementation' (Protocol in workflow.md) [checkpoint: ]

## Phase 4: Integration & Polish
- [ ] Task: Remove old filter widgets to reclaim space.
- [ ] Task: Ensure all buttons have tooltips and keyboard shortcuts still work.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Integration & Polish' (Protocol in workflow.md) [checkpoint: ]