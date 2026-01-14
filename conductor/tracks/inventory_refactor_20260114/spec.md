# Track Spec: Refactor Core Inventory Merging and Add Robust Error Handling

## Overview
The goal of this track is to harden the core inventory synchronization engine. Currently, the  logic handles merging data from multiple Excel sources. This refactor will introduce structured error handling, transaction-like safety for file operations, and improved performance for large datasets.

## Objectives
1.  **Robust Error Handling:** Wrap all file I/O and data processing in structured try-except blocks with detailed logging and user-facing alerts.
2.  **Transaction Safety:** Ensure that Excel writes only occur if data integrity is verified, and implement a "staged" write process to avoid corruption if the application crashes during a save.
3.  **Performance Optimization:** Refactor the Pandas merging logic to handle 10,000+ items more efficiently.
4.  **Deduplication Logic:** Formalize the IMEI deduplication and conflict resolution process.

## Key Changes
-   **File: core/inventory.py**
    -   Introduce a `safe_sync()` method.
    -   Implement comprehensive validation of Excel schema before merging.
    -   Add logging using the `activity_log` module.
-   **File: core/utils.py**
    -   Add helper functions for safe file writes and backups.

## Acceptance Criteria
-   The application can sync 10,000+ items in under 2 seconds.
-   Corrupt or locked Excel files do not crash the application and provide clear error messages.
-   All status changes (IN/OUT/RTN) are persistently saved even if the source Excel file is modified externally.
-   Code coverage for `core/inventory.py` exceeds 80%.
