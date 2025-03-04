#!/bin/bash
# Create GitHub issues for the v1.2.0 milestone
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ISSUES_DIR="$PROJECT_DIR/docs/issues"
REPO="fabioeloi/qemu-micropython"
MILESTONE="v1.2.0"

echo "Creating GitHub issues for the v1.2.0 milestone..."

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI not found. Please install it first."
    echo "See: https://cli.github.com/manual/installation"
    exit 1
fi

# Check if the user is authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: You are not authenticated with GitHub CLI."
    echo "Please run 'gh auth login' first."
    exit 1
fi

# Check if the milestone exists
MILESTONE_ID=$(gh api "repos/$REPO/milestones" --jq ".[] | select(.title == \"$MILESTONE\") | .number")
if [ -z "$MILESTONE_ID" ]; then
    echo "Milestone $MILESTONE not found. Creating it..."
    MILESTONE_ID=$(gh api "repos/$REPO/milestones" -X POST -f title="$MILESTONE" -f state="open" -f description="IoT and Simulation Capabilities" --jq ".number")
    echo "Created milestone $MILESTONE with ID $MILESTONE_ID"
else
    echo "Found milestone $MILESTONE with ID $MILESTONE_ID"
fi

# Create issues from the templates
for issue_file in "$ISSUES_DIR"/*.md; do
    if [ -f "$issue_file" ]; then
        echo "Processing issue template: $issue_file"
        
        # Extract issue title from the first line
        TITLE=$(head -n 1 "$issue_file" | sed 's/^# //')
        
        # Extract issue body (skip the first line)
        BODY=$(tail -n +2 "$issue_file")
        
        # Create the issue
        echo "Creating issue: $TITLE"
        ISSUE_URL=$(gh issue create --repo "$REPO" --title "$TITLE" --body "$BODY" --milestone "$MILESTONE_ID")
        
        echo "Created issue: $ISSUE_URL"
    fi
done

echo "All issues created successfully!"
echo "You can view them at: https://github.com/$REPO/milestone/$MILESTONE_ID" 