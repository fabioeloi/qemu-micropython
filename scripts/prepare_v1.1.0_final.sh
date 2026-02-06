#!/bin/bash
# Final release preparation script for v1.1.0
# This script prepares the repository for the v1.1.0 final release

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CURRENT_VERSION="v1.1.0-beta.5"
NEW_VERSION="v1.1.0"
RELEASE_DATE=$(date +"%Y-%m-%d")

echo -e "${BLUE}=========================================="
echo "v1.1.0 Final Release Preparation"
echo -e "==========================================${NC}"
echo ""
echo "This script will prepare the repository for the v1.1.0 final release."
echo "Current version: $CURRENT_VERSION"
echo "New version: $NEW_VERSION"
echo "Release date: $RELEASE_DATE"
echo ""

# Function to update version in a file
update_version_in_file() {
    local file=$1
    local old_version=$2
    local new_version=$3
    
    if [ -f "$file" ]; then
        if grep -q "$old_version" "$file"; then
            echo -e "${YELLOW}→${NC} Updating version in $file"
            sed -i "s/$old_version/$new_version/g" "$file"
            echo -e "${GREEN}✓${NC} Updated $file"
        else
            echo -e "${YELLOW}⚠${NC} $file does not contain $old_version"
        fi
    else
        echo -e "${RED}✗${NC} $file not found"
    fi
}

# Confirm before proceeding
echo -e "${YELLOW}Do you want to proceed with the release preparation? (y/n)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Release preparation cancelled."
    exit 0
fi
echo ""

echo -e "${BLUE}[1] Updating Version Numbers${NC}"
echo "-------------------------------------------"

# Update CURRENT_VERSION file
if [ -f "CURRENT_VERSION" ]; then
    echo "$NEW_VERSION" > CURRENT_VERSION
    echo -e "${GREEN}✓${NC} Updated CURRENT_VERSION"
else
    echo -e "${RED}✗${NC} CURRENT_VERSION file not found"
fi

# Update README.md
update_version_in_file "README.md" "$CURRENT_VERSION" "$NEW_VERSION"

# Update version references in ROADMAP_STATUS.md
if [ -f "ROADMAP_STATUS.md" ]; then
    echo -e "${YELLOW}→${NC} Updating version references in ROADMAP_STATUS.md"
    # Update specific version references while preserving historical ones
    sed -i "s/Current Release:.*$/Current Release: $NEW_VERSION/" ROADMAP_STATUS.md
    echo -e "${GREEN}✓${NC} Updated ROADMAP_STATUS.md"
fi

echo ""

echo -e "${BLUE}[2] Creating Final Release Notes${NC}"
echo "-------------------------------------------"

RELEASE_NOTES_FILE="docs/release_notes/$NEW_VERSION.md"

if [ -f "docs/release_notes/v1.1.0_template.md" ]; then
    echo -e "${YELLOW}→${NC} Creating release notes from template"
    cp "docs/release_notes/v1.1.0_template.md" "$RELEASE_NOTES_FILE"
    
    # Update date in release notes
    sed -i "s/Release Date: TBD/Release Date: $RELEASE_DATE/" "$RELEASE_NOTES_FILE"
    sed -i "s/\[Release date to be determined\]/Released: $RELEASE_DATE/" "$RELEASE_NOTES_FILE"
    
    echo -e "${GREEN}✓${NC} Created $RELEASE_NOTES_FILE"
else
    echo -e "${RED}✗${NC} Release notes template not found"
fi

echo ""

echo -e "${BLUE}[3] Updating VERSION_MAPPING.md${NC}"
echo "-------------------------------------------"

if [ -f "VERSION_MAPPING.md" ]; then
    echo -e "${YELLOW}→${NC} Adding v1.1.0 entry to VERSION_MAPPING.md"
    
    # Check if entry already exists
    if grep -q "| $NEW_VERSION |" VERSION_MAPPING.md; then
        echo -e "${YELLOW}⚠${NC} Entry already exists in VERSION_MAPPING.md"
    else
        # Add new entry (this is simplified - manual review recommended)
        echo "| $NEW_VERSION | $RELEASE_DATE | Final release of v1.1.0 milestone | Debugging and QEMU Integration |" >> VERSION_MAPPING.md
        echo -e "${GREEN}✓${NC} Added entry to VERSION_MAPPING.md"
    fi
else
    echo -e "${RED}✗${NC} VERSION_MAPPING.md not found"
fi

echo ""

echo -e "${BLUE}[4] Running Verification Tests${NC}"
echo "-------------------------------------------"

if [ -f "scripts/verify_v1.1.0_completion.sh" ]; then
    echo -e "${YELLOW}→${NC} Running v1.1.0 completion verification"
    if bash scripts/verify_v1.1.0_completion.sh; then
        echo -e "${GREEN}✓${NC} Verification passed"
    else
        echo -e "${RED}✗${NC} Verification failed - please review and fix issues"
        echo -e "${YELLOW}Continue anyway? (y/n)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Release preparation halted."
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠${NC} Verification script not found"
fi

echo ""

echo -e "${BLUE}[5] Checking for Uncommitted Changes${NC}"
echo "-------------------------------------------"

if git diff --quiet && git diff --cached --quiet; then
    echo -e "${GREEN}✓${NC} No uncommitted changes"
else
    echo -e "${YELLOW}⚠${NC} There are uncommitted changes:"
    git status --short
    echo ""
    echo -e "${YELLOW}These changes will need to be committed before tagging the release.${NC}"
fi

echo ""

echo -e "${BLUE}[6] Generating Release Summary${NC}"
echo "-------------------------------------------"

cat << EOF

===========================================
v1.1.0 Release Preparation Summary
===========================================

Version Updated: $CURRENT_VERSION → $NEW_VERSION
Release Date: $RELEASE_DATE

Files Updated:
  • CURRENT_VERSION
  • README.md
  • ROADMAP_STATUS.md
  • VERSION_MAPPING.md
  • Release Notes: $RELEASE_NOTES_FILE

Next Steps:
-----------
1. Review all updated files
2. Commit changes:
   git add .
   git commit -m "Prepare v1.1.0 final release"

3. Run final tests:
   ./scripts/build.sh
   ./scripts/run_qemu.sh
   ./scripts/debug_micropython.sh

4. Tag the release:
   git tag -a $NEW_VERSION -m "Release $NEW_VERSION - Debugging and QEMU Integration"
   git push origin $NEW_VERSION

5. Create GitHub release:
   - Go to: https://github.com/fabioeloi/qemu-micropython/releases/new
   - Tag: $NEW_VERSION
   - Title: "v1.1.0 - Debugging and QEMU Integration"
   - Description: Copy from $RELEASE_NOTES_FILE
   - Publish release

6. Update Issue #14:
   - Post completion comment from docs/issue_14_completion_comment.md
   - Close issue as completed

7. Announce the release:
   - Update README.md with release announcement
   - Post to community channels

===========================================

EOF

echo -e "${GREEN}✓ Release preparation complete!${NC}"
echo ""
echo -e "${YELLOW}Please review all changes before committing and tagging the release.${NC}"
echo ""
