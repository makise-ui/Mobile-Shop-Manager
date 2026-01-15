# Track Plan: Fix False Positive Conflicts in Quick Status

## Phase 1: Implementation
- [x] Task: Implement `Green Phase`: Update `gui/app.py`'s `show_screen` method to set `self.suppress_conflicts` to `True` when the screen key is `'status'`. This prevents the "Conflict Detected" dialog from interrupting high-speed status updates (IN/OUT/RTN). [ea12b91]
- [x] Task: Implement `Green Phase`: Verify `_check_conflicts` logic in `gui/app.py` to ensure it correctly checks `self.suppress_conflicts` before instantiating `ConflictResolutionDialog`. [ea12b91]

## Phase 2: Verification [checkpoint: ea12b91]
- [x] Task: Conductor - User Manual Verification 'Phase 2: Verification' (Protocol in workflow.md) [checkpoint: ea12b91]
