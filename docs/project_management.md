# Project Tracking Synchronization

## 1. Purpose of the Workflow

This document describes the GitHub Action workflow defined in `.github/workflows/sync-project-tracking.yml`. The primary purpose of this workflow is to automate parts of the project tracking process within the STM32 IoT Virtual Development Environment repository. It aims to react to changes in the repository, particularly updates to the `ROADMAP_STATUS.md` file, and subsequently update relevant GitHub issues or project milestones. This automation is directly related to addressing [Issue #13: Automated Project Tracking Updates](https://github.com/placeholder/issues/13).

The workflow is designed to reduce manual effort in keeping GitHub issues and milestones aligned with the documented progress in `ROADMAP_STATUS.md`.

## 2. Trigger Conditions

The workflow is configured to run under the following conditions:

-   **Push to `main` branch:** The workflow triggers on every push to the `main` branch.
-   **Specific Path Changes:** It specifically monitors changes in:
    -   `ROADMAP_STATUS.md`
    -   `docs/milestone_*.md` (any milestone document in the docs folder)
    -   `.github/workflows/sync-project-tracking.yml` (changes to the workflow itself)
    -   `scripts/sync_tracking.py`
    -   `scripts/check_milestones.py`

## 3. Key Actions Performed

The workflow executes several key actions, primarily through Python scripts:

### 3.1. `scripts/sync_tracking.py`

This script is responsible for synchronizing feature progress from `ROADMAP_STATUS.md` to specific GitHub issues.

-   **Reading `ROADMAP_STATUS.md`:**
    -   The script attempts to parse `ROADMAP_STATUS.md` to extract features and their corresponding progress percentages. It typically looks for lines formatted in a specific way (e.g., table rows in Markdown).

-   **Feature Mapping (`feature_mapping`):**
    -   It utilizes a predefined dictionary called `feature_mapping` within the script. This dictionary links keywords (representing features or components) to specific GitHub issue numbers.
    -   For example:
        ```python
        feature_mapping = {
            "Custom UART driver": 2, # Maps to Issue #2
            "Network simulation": 5,  # Maps to Issue #5
            # ... other mappings ...
        }
        ```

-   **Current Limitation & Incomplete Logic:**
    -   **Crucially, the logic for mapping specific file changes (other than direct `ROADMAP_STATUS.md` updates) to all the features listed in `ROADMAP_STATUS.md` and then updating their corresponding GitHub issues is currently incomplete.**
    -   While the script can parse `ROADMAP_STATUS.md` for progress, its ability to intelligently determine *which* feature's progress to update based on *which* files were changed is limited.
    -   The existing examples in `feature_mapping` (like "Custom UART driver" to Issue #2 and "Network simulation" to Issue #5) are processed if `ROADMAP_STATUS.md` itself changes or if the script is triggered by other means. However, a comprehensive mapping of all features from `ROADMAP_STATUS.md` to dedicated issues and logic to update them based on a broader set of relevant file changes (e.g., changes in `src/uart_driver/` updating the "Custom UART driver" issue) is not fully implemented. **More mappings and corresponding conditional logic are needed.**

-   **Commenting on Issue #13:**
    -   After its execution, the script attempts to post a summary comment on [Issue #13](https://github.com/placeholder/issues/13), detailing which features it processed (if any) and the progress percentages it found or updated.

### 3.2. `scripts/check_milestones.py`

This script focuses on overall milestone progress based on the status of issues within those milestones.

-   **Calculating Milestone Progress:**
    -   It fetches issues associated with active milestones in the GitHub repository.
    -   It calculates the overall progress of a milestone by comparing the number of open issues to the total number of issues (open + closed) within that milestone.

-   **Commenting on Issues:**
    -   If a milestone's progress (calculated as percentage of closed issues) reaches certain predefined thresholds (e.g., 25%, 50%, 75%, 100%), the script will post a comment.
    -   Currently, it comments on **all issues that have "tracking" in their title** within that specific milestone. This targeting mechanism is broad and might lead to comments on multiple issues rather than a central milestone overview or a dedicated milestone tracking issue.

### 3.3. `Update documentation if needed` Step

-   This step is currently a **placeholder** within the workflow file (`sync-project-tracking.yml`).
-   It suggests an intention to automate documentation updates based on changes, but the actual implementation (e.g., what documentation to update, how to generate content) is not yet defined or scripted.

## 4. How it Addresses Issue #13

This GitHub Action workflow (`sync-project-tracking.yml`) and its associated scripts (`sync_tracking.py`, `check_milestones.py`) represent the **current implementation for [Issue #13: Automated Project Tracking Updates](https://github.com/placeholder/issues/13)**.

It addresses parts of Issue #13 by:
-   Attempting to read `ROADMAP_STATUS.md` for progress.
-   Updating specific, pre-mapped issues with this progress.
-   Commenting on Issue #13 itself with a summary.
-   Calculating and reporting on overall milestone completion.

However, as highlighted in the "Current Limitation" section for `sync_tracking.py`, the automation is not yet comprehensive and requires further development to fully realize the goals of Issue #13.

## 5. Recommendations for Enhancement (to fully address Issue #13)

To make the project tracking synchronization more robust and fully address Issue #13, the following enhancements are recommended:

1.  **Complete `feature_mapping` in `sync_tracking.py`:**
    -   Ensure that every major feature and sub-feature listed in `ROADMAP_STATUS.md` has a corresponding entry in the `feature_mapping` dictionary, linking it to a dedicated GitHub issue number.

2.  **Expand Conditional Logic in `sync_tracking.py`:**
    -   Develop more sophisticated logic to determine which feature's progress needs updating based on the specific files changed in a commit. For example, changes in `src/lib/iot_client.py` might trigger an update for an "IoT Client Features" tracking issue.
    -   This might involve analyzing the commit's file list and matching paths to feature areas.

3.  **Dedicated Tracking Issues:**
    -   Consider creating specific "tracking issues" for each major feature or even for each milestone. These issues would serve as the canonical place for automated progress updates from the scripts, rather than commenting on general development issues.

4.  **Refine `check_milestones.py` Targeting:**
    -   Instead of commenting on all issues with "tracking" in the title, refine the script to:
        -   Update the description of the GitHub Milestone itself with the progress percentage.
        -   Or, comment on a single, dedicated "Milestone Tracking Issue" (e.g., "Milestone v1.2.0 Progress").

5.  **Define and Implement "Update documentation if needed":**
    -   Clarify the requirements for this step.
    -   If, for example, a milestone's completion should trigger an update to a `docs/milestones_completed.md` file, this logic should be scripted and integrated.

6.  **Error Handling and Idempotency:**
    -   Improve error handling in the scripts (e.g., if `ROADMAP_STATUS.md` parsing fails).
    -   Ensure scripts are idempotent where possible (i.e., running them multiple times with the same input doesn't produce unintended side effects like duplicate comments).

## 6. Monitoring

The activity and execution logs of the "Project Tracking Synchronization" workflow can be monitored under the **"Actions" tab** of the GitHub repository. This is useful for debugging any failures or verifying that the workflow is triggering and running as expected.

By implementing these enhancements, the workflow can become a much more powerful tool for automating project tracking and maintaining alignment between documentation and the project's status on GitHub.
