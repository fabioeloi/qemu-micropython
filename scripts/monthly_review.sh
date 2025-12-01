#!/bin/bash
# Monthly review automation script
# This script helps conduct monthly roadmap reviews

set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROADMAP_FILE="$PROJECT_DIR/ROADMAP_STATUS.md"
TEMPLATES_DIR="$PROJECT_DIR/docs/templates"
REVIEW_OUTPUT_DIR="$PROJECT_DIR/docs/reviews"
CURRENT_DATE=$(date +"%Y-%m-%d")
CURRENT_MONTH=$(date +"%B %Y")
REVIEW_FILE="$REVIEW_OUTPUT_DIR/monthly_review_$(date +%Y%m).md"

# Detect repository owner and name from git remote
get_repo_info() {
    local remote_url
    remote_url=$(git -C "$PROJECT_DIR" config --get remote.origin.url 2>/dev/null || echo "")
    
    if [ -z "$remote_url" ]; then
        echo ""
        return
    fi
    
    # Handle both HTTPS and SSH URLs
    # HTTPS: https://github.com/owner/repo.git
    # SSH: git@github.com:owner/repo.git
    if [[ "$remote_url" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
        echo "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    else
        echo ""
    fi
}

REPO_INFO=$(get_repo_info)
REPO_OWNER=$(echo "$REPO_INFO" | cut -d'/' -f1)
REPO_NAME=$(echo "$REPO_INFO" | cut -d'/' -f2)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to display section headers
section() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to display success messages
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to display warning messages
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to display error messages
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to display info messages
info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# Function to get file modification time (cross-platform)
get_file_mtime_date() {
    local file="$1"
    # Try GNU date first (Linux), then BSD date (macOS)
    local mtime
    if date -r "$file" "+%Y-%m-%d" 2>/dev/null; then
        return
    fi
    # Fallback: use stat
    local ts
    ts=$(stat -c %Y "$file" 2>/dev/null) || ts=$(stat -f %m "$file" 2>/dev/null) || ts=""
    if [ -n "$ts" ]; then
        date -d "@$ts" "+%Y-%m-%d" 2>/dev/null || echo "Unknown"
    else
        echo "Unknown"
    fi
}

# Cross-platform sed in-place edit
sed_inplace() {
    local pattern="$1"
    local file="$2"
    # Try GNU sed first, then BSD sed
    if sed --version 2>/dev/null | grep -q GNU; then
        sed -i "$pattern" "$file"
    else
        sed -i '' "$pattern" "$file"
    fi
}

# Create reviews directory if it doesn't exist
mkdir -p "$REVIEW_OUTPUT_DIR"

# Display welcome message
clear
section "Monthly Roadmap Review - $CURRENT_MONTH"

echo ""
echo "This script will guide you through the monthly roadmap review process."
echo "It will help you:"
echo "  1. Review milestone progress"
echo "  2. Update issue progress indicators"
echo "  3. Verify documentation synchronization"
echo "  4. Generate a review report"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Step 1: Run synchronization verification
section "Step 1: Synchronization Verification"

info "Running synchronization verification..."
if [ -x "$PROJECT_DIR/scripts/verify_sync.sh" ]; then
    bash "$PROJECT_DIR/scripts/verify_sync.sh" || true
    success "Synchronization verification complete"
else
    warning "verify_sync.sh not found or not executable"
fi

echo ""
read -p "Press Enter to continue to milestone progress..."

# Step 2: Fetch and display milestone progress
section "Step 2: Milestone Progress Review"

if command -v gh &> /dev/null && gh auth status &> /dev/null 2>&1; then
    info "Fetching milestone information from GitHub..."
    
    if [ -n "$REPO_OWNER" ] && [ -n "$REPO_NAME" ]; then
        milestones=$(gh api "repos/$REPO_OWNER/$REPO_NAME/milestones" --jq '.[] | "\(.title)|\(.open_issues)|\(.closed_issues)|\(.due_on // "none")"' 2>/dev/null || echo "")
    else
        warning "Could not determine repository info from git remote"
        milestones=""
    fi
    
    if [ -n "$milestones" ]; then
        echo ""
        echo "Current Milestone Status:"
        echo "┌──────────────┬──────────┬────────┬──────────┬──────────────┐"
        echo "│ Milestone    │ Progress │ Open   │ Closed   │ Due Date     │"
        echo "├──────────────┼──────────┼────────┼──────────┼──────────────┤"
        
        echo "$milestones" | while IFS='|' read -r title open closed due; do
            total=$((open + closed))
            if [ $total -gt 0 ]; then
                progress=$((closed * 100 / total))
            else
                progress=0
            fi
            due_display="${due:0:10}"
            printf "│ %-12s │ %6s%% │ %6s │ %8s │ %-12s │\n" "$title" "$progress" "$open" "$closed" "$due_display"
        done
        
        echo "└──────────────┴──────────┴────────┴──────────┴──────────────┘"
        success "Milestone progress fetched"
    else
        warning "No milestones found"
    fi
else
    warning "GitHub CLI not available - showing ROADMAP_STATUS.md progress"
    
    echo ""
    echo "Progress from ROADMAP_STATUS.md:"
    grep -E "^\| [A-Z].*\| [0-9]+%" "$ROADMAP_FILE" | head -20 || true
fi

echo ""
read -p "Press Enter to continue to issue review..."

# Step 3: Review issues
section "Step 3: Issue Progress Review"

if command -v gh &> /dev/null && gh auth status &> /dev/null 2>&1; then
    info "Fetching open issues..."
    
    echo ""
    echo "Open Issues by Milestone:"
    echo ""
    
    # Get issues grouped by milestone
    gh issue list --state open --limit 50 --json number,title,milestone,labels | \
        jq -r '.[] | "  #\(.number): \(.title) [\(.milestone.title // "No milestone")]"' 2>/dev/null || \
        warning "Unable to fetch issues"
    
    success "Issue review complete"
else
    warning "GitHub CLI not available - skipping issue review"
fi

echo ""
read -p "Press Enter to continue to documentation check..."

# Step 4: Documentation consistency check
section "Step 4: Documentation Consistency Check"

info "Checking documentation files..."

docs_to_check=(
    "ROADMAP_STATUS.md"
    "VERSION_MAPPING.md"
    "README.md"
    "docs/SYNC_PROCESS.md"
)

echo ""
echo "Documentation Status:"
echo "┌────────────────────────────┬──────────────────────┬──────────┐"
echo "│ Document                   │ Last Modified        │ Status   │"
echo "├────────────────────────────┼──────────────────────┼──────────┤"

for doc in "${docs_to_check[@]}"; do
    doc_path="$PROJECT_DIR/$doc"
    if [ -f "$doc_path" ]; then
        # Get last modified date using cross-platform function
        last_mod=$(get_file_mtime_date "$doc_path")
        
        # Check age - get modification timestamp
        last_mod_ts=$(stat -c %Y "$doc_path" 2>/dev/null) || last_mod_ts=$(stat -f %m "$doc_path" 2>/dev/null) || last_mod_ts=0
        current_ts=$(date +%s)
        
        if [ "$last_mod_ts" -gt 0 ]; then
            days_old=$(( (current_ts - last_mod_ts) / 86400 ))
        else
            days_old=999
        fi
        
        if [ $days_old -lt 30 ]; then
            status="✓ Current"
        else
            status="⚠ Review"
        fi
        
        printf "│ %-26s │ %-20s │ %-8s │\n" "$doc" "$last_mod" "$status"
    else
        printf "│ %-26s │ %-20s │ %-8s │\n" "$doc" "N/A" "✗ Missing"
    fi
done

echo "└────────────────────────────┴──────────────────────┴──────────┘"

echo ""
read -p "Press Enter to generate review report..."

# Step 5: Generate review report
section "Step 5: Generating Review Report"

info "Creating review report from template..."

# Copy template and fill in basic information
if [ -f "$TEMPLATES_DIR/monthly_review_template.md" ]; then
    cp "$TEMPLATES_DIR/monthly_review_template.md" "$REVIEW_FILE"
    
    # Replace placeholders using cross-platform sed
    sed_inplace "s/\[MONTH YEAR\]/$CURRENT_MONTH/g" "$REVIEW_FILE"
    sed_inplace "s/\[DATE\]/$CURRENT_DATE/g" "$REVIEW_FILE"
    
    success "Review report created: $REVIEW_FILE"
else
    # Create a basic report
    cat > "$REVIEW_FILE" << EOF
# Monthly Roadmap Review - $CURRENT_MONTH

## Review Date: $CURRENT_DATE

## Summary

This review was generated by the monthly review script.

## Action Items

- [ ] Review milestone progress
- [ ] Update issue progress indicators
- [ ] Verify documentation synchronization
- [ ] Complete detailed review report

## Next Steps

Please complete this report with detailed findings from the review.

---

*Generated by monthly_review.sh on $CURRENT_DATE*
EOF
    success "Basic review report created: $REVIEW_FILE"
fi

# Final summary
section "Monthly Review Summary"

echo ""
echo "Review process complete!"
echo ""
echo "Generated files:"
echo "  • Review report: $REVIEW_FILE"
echo ""
echo "Next steps:"
echo "  1. Edit the review report with detailed findings"
echo "  2. Update any outdated documentation"
echo "  3. Update issue progress percentages in GitHub"
echo "  4. Commit changes to repository"
echo ""
echo "To update issue progress in GitHub:"
echo "  gh issue edit <number> --add-label 'progress-updated'"
echo "  gh issue comment <number> --body 'Progress update: X%'"
echo ""

success "Monthly review process complete!"
