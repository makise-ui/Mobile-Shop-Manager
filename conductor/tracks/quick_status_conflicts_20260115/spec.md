# Track Spec: Fix False Positive Conflicts in Quick Status

## Overview
The "Quick Status" screen triggers a "Conflict Detected" popup every time an item status is updated (IN/OUT/RTN), even in single-user mode. This appears to be a false positive where the application detects its own file write (during the update) as an external modification, triggering a conflict check that shouldn't happen or should be auto-resolved. The user currently has to press "Ignore" to proceed, which is disruptive.

## Functional Requirements
1.  **Suppress Self-Induced Conflicts:** The application must distinguish between file changes caused by its own `update_status` operations and genuine external changes (e.g., another user saving the Excel file).
2.  **Quick Status Screen:** When updating an item's status (Single or Batch mode), the operation should complete silently without showing a conflict dialog if the "conflict" was merely the result of the immediate write.
3.  **Data Integrity:** Genuine external conflicts (e.g., file changed by someone else *before* we wrote our update) must still be handled or at least safe-guarded, but the immediate read-back of our own write should be trusted.

## Non-Functional Requirements
*   **User Experience:** Eliminate the "Conflict Detected" popup for standard workflows in Quick Status.

## Out of Scope
*   Rewriting the entire file watching architecture (unless necessary for the fix).
*   Changes to other screens (Inventory/Billing) unless they share the same broken logic.
