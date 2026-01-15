# Track Spec: Inventory UI Overhaul - Advanced Filters & Compact Icons

## Overview
This feature aims to declutter the Inventory screen by replacing the standard filter inputs with a collapsible Advanced Filter panel and reducing the visual footprint of action buttons using compact icon-based designs.

## Functional Requirements
1.  **Advanced Filter Panel:**
    *   Implement a collapsible panel (toggled via a "Filter" button) to house all filter controls.
    *   **Multi-Criteria Filtering:** Support combining Status, Price Range, Model, Supplier, and Date Ranges.
    *   **Specific Filters:**
        *   **Date Range:** "Date Added" and "Date Sold" selection.
        *   **Supplier:** Dropdown/Multi-select for supplier filtering.
    *   **Real-time vs. Apply:** Decided: Filters apply on "Apply" button click or enter key to avoid lag (or real-time if performance permits). *Recommendation: Apply button for complex multi-filters.*

2.  **Compact Action Toolbar:**
    *   Replace large text buttons (Add, Print, Delete, Refresh) with small, icon-only or icon+tooltip buttons.
    *   Use **Bootstrap Icons** (via `ttkbootstrap` or assets) for consistency.
    *   Ensure tooltips are present for usability.

## Non-Functional Requirements
*   **Space Efficiency:** The changes must significantly increase the vertical screen real estate available for the inventory grid.
*   **Responsiveness:** The filter panel animation/toggle should be smooth.

## UI/UX
*   **Toolbar:** A thin strip containing the "Filter" toggle and the compact action icons.
*   **Icons:** Standard Bootstrap-style icons.

## Out of Scope
*   Changes to the underlying inventory data structure (only UI filtering logic).
*   Changes to the "Billing" or "Settings" screens.