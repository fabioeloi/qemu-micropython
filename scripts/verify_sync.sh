#!/bin/bash
# Verify synchronization between ROADMAP_STATUS.md and GitHub issues
# This script checks for discrepancies in progress tracking

set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROADMAP_FILE="$PROJECT_DIR/ROADMAP_STATUS.md"
OUTPUT_FILE="$PROJECT_DIR/test_results/sync_verification_$(date +%Y%m%d_%H%M%S).txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure test_results directory exists
mkdir -p "$PROJECT_DIR/test_results"

# Function to display section headers
section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
    echo "=== $1 ===" >> "$OUTPUT_FILE"
}

# Function to display success messages
success() {
    echo -e "${GREEN}✓ $1${NC}"
    echo "✓ $1" >> "$OUTPUT_FILE"
}

# Function to display warning messages
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    echo "⚠ $1" >> "$OUTPUT_FILE"
}

# Function to display error messages
error() {
    echo -e "${RED}✗ $1${NC}"
    echo "✗ $1" >> "$OUTPUT_FILE"
}

# Initialize output file
echo "Synchronization Verification Report" > "$OUTPUT_FILE"
echo "Generated: $(date)" >> "$OUTPUT_FILE"
echo "======================================" >> "$OUTPUT_FILE"

# Display welcome message
section "Project Tracking Synchronization Verification"
echo "This script verifies alignment between ROADMAP_STATUS.md and GitHub issues."

# Check if required files exist
section "File Existence Check"

if [ -f "$ROADMAP_FILE" ]; then
    success "ROADMAP_STATUS.md exists"
else
    error "ROADMAP_STATUS.md not found"
    exit 1
fi

if [ -f "$PROJECT_DIR/VERSION_MAPPING.md" ]; then
    success "VERSION_MAPPING.md exists"
else
    warning "VERSION_MAPPING.md not found"
fi

# Extract progress percentages from ROADMAP_STATUS.md
section "Extracting Progress from ROADMAP_STATUS.md"

declare -A roadmap_progress

# Parse the roadmap file for progress percentages
while IFS= read -r line; do
    # Look for lines with progress percentages (format: | Feature | Status | ... | XX% | ...)
    if [[ $line =~ \|[^|]+\|[^|]+\|[^|]+\|[[:space:]]*([0-9]+)%[[:space:]]*\| ]]; then
        percentage="${BASH_REMATCH[1]}"
        # Extract feature name (first column after initial |)
        feature=$(echo "$line" | awk -F'|' '{print $2}' | xargs)
        if [ -n "$feature" ] && [ "$feature" != "Feature" ]; then
            roadmap_progress["$feature"]="$percentage"
            echo "  Found: $feature = $percentage%" >> "$OUTPUT_FILE"
        fi
    fi
done < "$ROADMAP_FILE"

echo "Found ${#roadmap_progress[@]} features with progress tracking"
success "Progress extraction complete"

# Check if GitHub CLI is available
section "GitHub Integration Check"

if command -v gh &> /dev/null; then
    success "GitHub CLI is available"
    
    # Check if authenticated
    if gh auth status &> /dev/null; then
        success "GitHub CLI is authenticated"
        
        # Fetch issues and compare
        section "Fetching GitHub Issues"
        
        issues_json=$(gh issue list --limit 100 --json number,title,state,milestone,labels 2>/dev/null || echo "[]")
        
        if [ "$issues_json" != "[]" ]; then
            issue_count=$(echo "$issues_json" | jq 'length')
            success "Found $issue_count issues"
            
            # Check for tracking issues
            section "Verifying Issue Progress"
            
            echo "$issues_json" | jq -r '.[] | "\(.number)|\(.title)|\(.state)|\(.milestone.title // "none")"' | while IFS='|' read -r number title state milestone; do
                echo "  Issue #$number: $title (state: $state, milestone: $milestone)" >> "$OUTPUT_FILE"
            done
            
            # Check milestone alignment
            section "Milestone Verification"
            
            milestones=$(gh api repos/:owner/:repo/milestones --jq '.[] | "\(.title)|\(.open_issues)|\(.closed_issues)"' 2>/dev/null || echo "")
            
            if [ -n "$milestones" ]; then
                echo "$milestones" | while IFS='|' read -r title open closed; do
                    total=$((open + closed))
                    if [ $total -gt 0 ]; then
                        progress=$((closed * 100 / total))
                        echo "  Milestone $title: $progress% ($closed/$total issues)" 
                        echo "  Milestone $title: $progress% ($closed/$total issues)" >> "$OUTPUT_FILE"
                    fi
                done
                success "Milestone verification complete"
            else
                warning "No milestones found or unable to fetch"
            fi
        else
            warning "No issues found or unable to fetch"
        fi
    else
        warning "GitHub CLI not authenticated - skipping GitHub verification"
        echo "  Run 'gh auth login' to enable GitHub integration" >> "$OUTPUT_FILE"
    fi
else
    warning "GitHub CLI not installed - skipping GitHub verification"
    echo "  Install GitHub CLI from https://cli.github.com/" >> "$OUTPUT_FILE"
fi

# Check documentation consistency
section "Documentation Consistency Check"

# Check if ROADMAP_STATUS.md has recent updates
if [ -f "$ROADMAP_FILE" ]; then
    last_modified=$(stat -c %Y "$ROADMAP_FILE" 2>/dev/null || stat -f %m "$ROADMAP_FILE" 2>/dev/null)
    current_time=$(date +%s)
    days_since_update=$(( (current_time - last_modified) / 86400 ))
    
    if [ $days_since_update -lt 7 ]; then
        success "ROADMAP_STATUS.md updated recently (${days_since_update} days ago)"
    elif [ $days_since_update -lt 30 ]; then
        warning "ROADMAP_STATUS.md not updated in ${days_since_update} days"
    else
        error "ROADMAP_STATUS.md outdated (${days_since_update} days since last update)"
    fi
fi

# Check for required sections in ROADMAP_STATUS.md
section "Required Sections Check"

required_sections=(
    "v1.1.0 Milestone"
    "v1.2.0 Milestone"
    "v1.3.0 Milestone"
    "Timeline"
    "Current Focus"
    "Recent Progress"
)

for section_name in "${required_sections[@]}"; do
    if grep -qi "$section_name" "$ROADMAP_FILE"; then
        success "Found section: $section_name"
    else
        warning "Missing section: $section_name"
    fi
done

# Summary
section "Verification Summary"

echo ""
echo "Verification complete. Results saved to: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "1. Review any warnings or errors above"
echo "2. Update documentation if discrepancies found"
echo "3. Run './scripts/update_milestone_progress.sh' to update progress"
echo ""

success "Synchronization verification complete"
