# Track Plan: Refactor Core Inventory Merging and Add Robust Error Handling

## Phase 1: Foundation & Diagnostics [checkpoint: 1cec6f3]
- [x] Task: Audit current `core/inventory.py` and identify critical failure points. [19354e6]
- [x] Task: Create a comprehensive test suite for current merging logic (expect failures in edge cases). [e33521e]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Foundation & Diagnostics' (Protocol in workflow.md) [checkpoint: 1cec6f3]

## Phase 2: Refactor Merging Logic
- [ ] Task: Implement `Red Phase`: Write failing tests for large dataset merging and schema mismatch handling.
- [ ] Task: Implement `Green Phase`: Refactor merging logic using optimized Pandas operations.
- [ ] Task: Implement `Red Phase`: Write failing tests for locked file scenarios.
- [ ] Task: Implement `Green Phase`: Add robust file locking detection and retry mechanisms.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Refactor Merging Logic' (Protocol in workflow.md) [checkpoint: ]

## Phase 3: Data Integrity & Safety
- [ ] Task: Implement `Red Phase`: Write failing tests for data loss during interrupted save.
- [ ] Task: Implement `Green Phase`: Implement staged write (write to temp, then rename) and automatic backups.
- [ ] Task: Implement `Red Phase`: Write failing tests for IMEI collision resolution.
- [ ] Task: Implement `Green Phase`: Refine the conflict resolution dialog and auto-merge logic.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Data Integrity & Safety' (Protocol in workflow.md) [checkpoint: ]

## Phase 4: Verification & Polishing
- [ ] Task: Finalize documentation for the new sync engine.
- [ ] Task: Achieve >80% code coverage for all modified core modules.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Verification & Polishing' (Protocol in workflow.md) [checkpoint: ]
