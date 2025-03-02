#!/bin/bash
# Update milestone progress in the roadmap status document
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROADMAP_FILE="$PROJECT_DIR/ROADMAP_STATUS.md"

echo "Updating milestone progress tracking..."

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI not found. Please install it first."
    exit 1
fi

# Get milestone information
echo "Fetching milestone information..."
milestones=$(gh api repos/fabioeloi/qemu-micropython/milestones --jq '.[].title, .[].description, .[].open_issues, .[].closed_issues')

# Parse and update the roadmap status file
echo "Updating roadmap status file: $ROADMAP_FILE"

# Get all issues with their labels and milestone
echo "Fetching detailed issue information..."
all_issues=$(gh issue list --limit 100 --json title,milestone,labels,state)

# Create a backup of the roadmap file
cp "$ROADMAP_FILE" "${ROADMAP_FILE}.bak"

# Extract milestone information
v110_total=$(echo "$all_issues" | jq -r '[.[] | select(.milestone.title == "v1.1.0")] | length')
v110_closed=$(echo "$all_issues" | jq -r '[.[] | select(.milestone.title == "v1.1.0" and .state == "closed")] | length')
v110_percent=$((v110_closed * 100 / v110_total))

v120_total=$(echo "$all_issues" | jq -r '[.[] | select(.milestone.title == "v1.2.0")] | length')
v120_closed=$(echo "$all_issues" | jq -r '[.[] | select(.milestone.title == "v1.2.0" and .state == "closed")] | length')
v120_percent=$((v120_closed * 100 / v120_total))

v130_total=$(echo "$all_issues" | jq -r '[.[] | select(.milestone.title == "v1.3.0")] | length')
v130_closed=$(echo "$all_issues" | jq -r '[.[] | select(.milestone.title == "v1.3.0" and .state == "closed")] | length')
v130_percent=$((v130_closed * 100 / v130_total))

# Print updated milestone information
echo "Milestone Progress:"
echo "v1.1.0: $v110_percent% ($v110_closed/$v110_total issues completed)"
echo "v1.2.0: $v120_percent% ($v120_closed/$v120_total issues completed)"
echo "v1.3.0: $v130_percent% ($v130_closed/$v130_total issues completed)"

echo "Milestone progress tracking updated."
echo "You can now manually update the ROADMAP_STATUS.md file with this information"
echo "or implement automatic updating in future versions of this script."

# Future enhancement: Use sed to automatically update the ROADMAP_STATUS.md file
# with the percentage values calculated above 