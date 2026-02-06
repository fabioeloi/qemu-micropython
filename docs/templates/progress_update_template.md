# Progress Update Template

Use this template when adding progress updates to GitHub issues.

---

## Progress Update - [DATE]

### Current Progress: [PERCENTAGE]%

### Changes Made

- [Description of change 1]
- [Description of change 2]
- [Description of change 3]

### Commits/PRs

- [Link to commit/PR 1]
- [Link to commit/PR 2]

### What's Next

- [Next task 1]
- [Next task 2]

### Blockers/Challenges

- [Blocker 1, if any]
- None

### Related Issues

- Relates to #[issue_number]
- Blocks #[issue_number]
- Depends on #[issue_number]

---

## Usage Instructions

1. Copy the template above (between the `---` markers)
2. Replace placeholders with actual values:
   - `[DATE]`: Current date (YYYY-MM-DD format)
   - `[PERCENTAGE]`: Updated progress percentage (0-100)
   - `[Description]`: Specific changes made
   - `[Link]`: Full URLs to commits or PRs
   - `[issue_number]`: Related issue numbers
3. Post as a comment on the relevant issue
4. Update the issue progress if significant change

## Progress Percentage Guidelines

| Range | Description |
|-------|-------------|
| 0-10% | Issue accepted, initial planning |
| 10-25% | Initial implementation started |
| 25-50% | Core functionality implemented |
| 50-75% | Tests and documentation added |
| 75-90% | Bug fixes and refinements |
| 90-99% | Final review and polish |
| 100% | Complete and verified |

## Example

```markdown
## Progress Update - 2025-03-15

### Current Progress: 75%

### Changes Made

- Implemented core UART simulation features
- Added error injection capabilities
- Created unit tests for all new functions

### Commits/PRs

- https://github.com/fabioeloi/qemu-micropython/commit/abc1234
- https://github.com/fabioeloi/qemu-micropython/pull/42

### What's Next

- Add documentation for new features
- Integrate with existing test framework
- Performance optimization

### Blockers/Challenges

- Need clarification on buffer size limits

### Related Issues

- Relates to #5
- Blocks #12
```
