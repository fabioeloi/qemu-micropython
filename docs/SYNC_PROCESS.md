# Project Tracking Synchronization Process

This document describes the regular process to keep project tracking documents and GitHub issues synchronized.

## Overview

Maintaining consistency between documentation (ROADMAP_STATUS.md, VERSION_MAPPING.md) and GitHub issues is essential for project transparency and team coordination. This process ensures that all tracking documents reflect the current state of the project.

## Automated Synchronization

### GitHub Actions Workflow

The `sync-project-tracking.yml` workflow automatically runs on pushes to main when changes occur in:
- `src/**` - Source code changes
- `docs/**` - Documentation changes
- `scripts/**` - Script changes
- `tests/**` - Test changes
- `ROADMAP_STATUS.md` - Roadmap updates
- `VERSION_MAPPING.md` - Version mapping updates
- `README.md` - README updates

The workflow performs:
1. Analyzes commit changes
2. Updates relevant issues with progress information
3. Checks milestone progress
4. Posts tracking sync reports

### Manual Scripts

#### Update Milestone Progress
```bash
./scripts/update_milestone_progress.sh
```
This script:
- Fetches milestone information from GitHub
- Calculates progress percentages based on open/closed issues
- Reports current milestone status

#### Verify Synchronization
```bash
./scripts/verify_sync.sh
```
This script:
- Verifies alignment between ROADMAP_STATUS.md and GitHub issues
- Checks for discrepancies in progress percentages
- Reports any inconsistencies

## After Each Significant Commit

### Checklist

After making a significant commit that affects project progress:

- [ ] **Update affected issues** with progress percentages
  - Use the issue progress template (see [Templates](#templates))
  - Include specific changes made
  - Update completion percentage

- [ ] **Add detailed progress updates** to relevant issues
  - Describe what was accomplished
  - Note any blockers or challenges
  - Link to related commits or PRs

- [ ] **Update ROADMAP_STATUS.md** if progress changes
  - Update the progress percentage in the feature table
  - Add notes about the current status
  - Update "Recent Progress Updates" section if significant

- [ ] **Verify synchronization** between documentation and issues
  - Run `./scripts/verify_sync.sh`
  - Address any discrepancies reported

### Progress Update Guidelines

1. **Increment progress** when:
   - A sub-feature is completed
   - Tests are added and passing
   - Documentation is updated
   - Bug fixes are implemented

2. **Progress percentage guidance**:
   - 0-25%: Initial implementation started
   - 25-50%: Core functionality implemented
   - 50-75%: Tests and documentation added
   - 75-90%: Bug fixes and refinements
   - 90-100%: Final review and polish

## Monthly Review Process

### Schedule

Monthly reviews should be conducted on the first week of each month.

### Monthly Review Checklist

Run the monthly review script or follow this manual checklist:

```bash
./scripts/monthly_review.sh
```

#### Manual Checklist

- [ ] **Hold roadmap review session**
  - Review all milestone progress
  - Discuss blockers and challenges
  - Adjust priorities if needed

- [ ] **Update all issue progress indicators**
  - Review each open issue
  - Update progress percentages
  - Add monthly progress comments

- [ ] **Verify milestone progress**
  - Check milestone completion rates
  - Update milestone due dates if needed
  - Identify at-risk milestones

- [ ] **Update documentation to reflect actual progress**
  - Review ROADMAP_STATUS.md accuracy
  - Update VERSION_MAPPING.md if needed
  - Review release notes

- [ ] **Check for discrepancies**
  - Run `./scripts/verify_sync.sh`
  - Fix any inconsistencies
  - Document any intentional differences

### Monthly Review Report Template

Use the template at `docs/templates/monthly_review_template.md` for documenting the review.

## Templates

### Issue Progress Update Template

Located at: `docs/templates/progress_update_template.md`

Use this template when adding progress comments to issues.

### Monthly Review Report Template

Located at: `docs/templates/monthly_review_template.md`

Use this template for documenting monthly review outcomes.

### Commit Tracking Template

Located at: `docs/templates/commit_tracking_template.md`

Use this template for significant commits that affect project progress.

## Success Criteria

The synchronization process is successful when:

1. **Regular updates to issues** reflecting current progress
2. **Consistent alignment** between roadmap and issues
3. **Up-to-date documentation** matching implementation status
4. **Clear tracking** of milestone progress

## Related Documents

- [ROADMAP_STATUS.md](../ROADMAP_STATUS.md) - Project roadmap and progress
- [VERSION_MAPPING.md](../VERSION_MAPPING.md) - Version mapping guide
- [Release Notes](release_notes/) - Release documentation

## Troubleshooting

### Common Issues

1. **Workflow not triggering**
   - Check that changes are in watched paths
   - Verify branch is main
   - Check Actions tab for errors

2. **Progress percentages don't match**
   - Run verification script
   - Manually reconcile differences
   - Update both documentation and issues

3. **Missing milestone updates**
   - Ensure issues are assigned to milestones
   - Check milestone existence in GitHub
   - Verify API access in workflows

### Getting Help

If you encounter issues with the synchronization process:
1. Check the GitHub Actions logs
2. Review the verification script output
3. Open an issue with the "infrastructure" label

## Changelog

- **Initial Version**: Established synchronization process documentation
