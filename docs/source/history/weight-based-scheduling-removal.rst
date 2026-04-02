Legacy Weight-Based Scheduling
==============================

*Removed January 2026 (Issue #3267)*

We used to have complicated system that calculated "weight" for every repository to decide which ones to update first. It looked at issue counts, PRs, and how "stale" the data was.

Honestly, it was overly complex. It made code harder to read and didn't seemingly improve performance enough to justify the complexity.

**What we changed:**
We deleted weight columns (`core_weight`, `facade_weight`, etc) and all math functions associated with them.

**How it works now:**
We kept it simple. We order repositories based on `issue_pr_sum` (total activity) and `commit_sum`. Active repos get updated; stale ones get their turn eventually. 
