# Product Guidelines: Mobile Shop Manager

## 1. Development Philosophy
*   **Reliability First:** As an inventory and billing tool, the application must prioritize data integrity and stability above all else. Every feature should be "safe-by-default."
*   **Pragmatic Quality:** Maintain a balance between modular, well-documented code and the pragmatic need to deliver functional features.

## 2. Visual Identity & UI/UX
*   **Professional & Functional:** Use clean, high-contrast layouts. Prefer standard Windows and Bootstrap-inspired patterns that prioritize data density and readability.
*   **Density for Power Users:** UI should maximize information visibility while remaining organized, catering to users who perform high-volume transactions.

## 3. Code Standards
*   **Modular Architecture:** Maintain strict separation between core business logic and the GUI layer.
*   **Defensive Programming:** Use comprehensive error handling, type hinting, and clear docstrings to ensure the codebase remains maintainable and robust.
*   **Verified Logic:** Aim for high test coverage for core inventory and billing calculations.

## 4. Data Integrity & Safety
*   **Checkpointing:** Automatically backup data files before any write operation.
*   **Audit Trail:** Maintain persistent, timestamped activity logs for all significant user and system actions.
*   **Fail-Safe Operations:** If a critical error occurs (e.g., file lock, data corruption), the app must alert the user and halt the operation to prevent data loss.

## 5. User Support
*   **Interactive Assistance:** Provide help directly within the application via context-aware tooltips and a dedicated interactive Markdown help system accessible via keyboard shortcuts (F1).
