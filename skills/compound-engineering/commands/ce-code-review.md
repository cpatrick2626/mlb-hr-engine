# /ce-code-review

## Purpose

Review completed or claimed-complete work against scope, definition of done, and regression risk.

## Required Output

```md
## /ce-code-review Result

### Claimed Work
...

### Files Changed
...

### Scope Check
PASS / FAIL

### Definition of Done Check
| Requirement | Status | Evidence |
|---|---|---|

### Regression Risk
...

### Validation Evidence
...

### Issues Found
- ...

### Recommendation
ACCEPT / REVISE / REJECT

### One Next Action
...
```

## Rule

If validation is missing, status cannot be ACCEPT.
