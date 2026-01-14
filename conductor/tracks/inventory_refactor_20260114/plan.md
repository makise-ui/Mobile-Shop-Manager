# Track Plan: Refactor Core Inventory Merging and Add Robust Error Handling

## Phase 1: Foundation & Diagnostics [checkpoint: 1cec6f3]
- [x] Task: Audit current `core/inventory.py` and identify critical failure points. [19354e6]
- [x] Task: Create a comprehensive test suite for current merging logic (expect failures in edge cases). [e33521e]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Foundation & Diagnostics' (Protocol in workflow.md) [checkpoint: 1cec6f3]

## Phase 2: Refactor Merging Logic [checkpoint: e91c29a]
- [x] Task: Implement `Red Phase`: Write failing tests for large dataset merging and schema mismatch handling. [86fd2e3]
- [x] Task: Implement `Green Phase`: Refactor merging logic using optimized Pandas operations. [6fa2143]
- [x] Task: Implement `Red Phase`: Write failing tests for locked file scenarios. [1cc1761]
- [x] Task: Implement `Green Phase`: Add robust file locking detection and retry mechanisms. [c4682f3]
- [x] Task: Conductor - User Manual Verification 'Phase 2: Refactor Merging Logic' (Protocol in workflow.md) [checkpoint: e91c29a]

## Phase 3: Data Integrity & Safety [checkpoint: 6baf6b2]
- [x] Task: Implement `Red Phase`: Write failing tests for data loss during interrupted save. [237c80b]
- [x] Task: Implement `Green Phase`: Implement staged write (write to temp, then rename) and automatic backups. [f3df196]
- [x] Task: Implement `Red Phase`: Write failing tests for IMEI collision resolution. [46567a4]
- [x] Task: Implement `Green Phase`: Refine the conflict resolution dialog and auto-merge logic. [6baf6b2]
- [x] Task: Conductor - User Manual Verification 'Phase 3: Data Integrity & Safety' (Protocol in workflow.md) [checkpoint: 6baf6b2]

## Phase 4: Verification & Polishing [checkpoint: 9dff97f]
- [x] Task: Finalize documentation for the new sync engine. [9dff97f]
- [x] Task: Achieve >80% code coverage for all modified core modules. [9dff97f]
- [x] Task: Conductor - User Manual Verification 'Phase 4: Verification & Polishing' (Protocol in workflow.md) [checkpoint: 9dff97f]
