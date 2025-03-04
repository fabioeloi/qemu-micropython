#!/bin/bash
# Script to prepare for the final v1.1.0 release
# This script automates the process of preparing for a release by:
# 1. Updating version files
# 2. Creating release notes
# 3. Running tests
# 4. Preparing for tagging

set -e

# Configuration
PROJECT_DIR=$(pwd)
CURRENT_DATE=$(date +"%Y.%m.%d")
CURRENT_VERSION_FILE="CURRENT_VERSION"
VERSION_MAPPING_FILE="VERSION_MAPPING.md"
README_FILE="README.md"
RELEASE_NOTES_DIR="docs/release_notes"
RELEASE_NOTES_TEMPLATE="$RELEASE_NOTES_DIR/v1.1.0_template.md"
TESTS_DIR="tests"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display section headers
section() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
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

# Check if we're in the project root
if [ ! -f "$CURRENT_VERSION_FILE" ]; then
    error "This script must be run from the project root directory"
    exit 1
fi

# Display welcome message
section "Preparing for v1.1.0 Final Release"
echo "This script will guide you through the process of preparing for the final v1.1.0 release."
echo "Make sure you have committed all your changes before proceeding."
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Check for uncommitted changes
section "Checking for uncommitted changes"
if [ -n "$(git status --porcelain)" ]; then
    warning "You have uncommitted changes. It's recommended to commit them before proceeding."
    read -p "Press Enter to continue anyway or Ctrl+C to cancel..."
else
    success "No uncommitted changes found"
fi

# Update version files
section "Updating version files"

# Read current version
DATE_VERSION=$(head -n 1 "$CURRENT_VERSION_FILE")
SEMANTIC_VERSION=$(tail -n 1 "$CURRENT_VERSION_FILE")

echo "Current version: $DATE_VERSION ($SEMANTIC_VERSION)"

# Generate new version
NEW_DATE_VERSION="v$CURRENT_DATE.1"
NEW_SEMANTIC_VERSION="v1.1.0"

echo "New version will be: $NEW_DATE_VERSION ($NEW_SEMANTIC_VERSION)"
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Update CURRENT_VERSION file
echo "$NEW_DATE_VERSION" > "$CURRENT_VERSION_FILE"
echo "$NEW_SEMANTIC_VERSION" >> "$CURRENT_VERSION_FILE"
success "Updated $CURRENT_VERSION_FILE"

# Update VERSION_MAPPING.md
sed -i '' "s/^| $DATE_VERSION | $SEMANTIC_VERSION |/| $NEW_DATE_VERSION | $NEW_SEMANTIC_VERSION |/" "$VERSION_MAPPING_FILE"
echo "| $NEW_DATE_VERSION | $NEW_SEMANTIC_VERSION | Final v1.1.0 release with complete debugging and QEMU integration features |" >> "$VERSION_MAPPING_FILE"
success "Updated $VERSION_MAPPING_FILE"

# Update README.md
sed -i '' "s/Current Version: $DATE_VERSION ($SEMANTIC_VERSION)/Current Version: $NEW_DATE_VERSION ($NEW_SEMANTIC_VERSION)/" "$README_FILE"
success "Updated $README_FILE"

# Create release notes
section "Creating release notes"

# Create release notes directory if it doesn't exist
mkdir -p "$RELEASE_NOTES_DIR"

# Create release notes file
RELEASE_NOTES_FILE="$RELEASE_NOTES_DIR/${NEW_DATE_VERSION}.md"

if [ -f "$RELEASE_NOTES_TEMPLATE" ]; then
    cp "$RELEASE_NOTES_TEMPLATE" "$RELEASE_NOTES_FILE"
    sed -i '' "s/VERSION_PLACEHOLDER/$NEW_DATE_VERSION ($NEW_SEMANTIC_VERSION)/" "$RELEASE_NOTES_FILE"
    sed -i '' "s/DATE_PLACEHOLDER/$(date +"%B %d, %Y")/" "$RELEASE_NOTES_FILE"
    success "Created release notes from template: $RELEASE_NOTES_FILE"
else
    warning "Release notes template not found: $RELEASE_NOTES_TEMPLATE"
    echo "# Release Notes: $NEW_DATE_VERSION ($NEW_SEMANTIC_VERSION)" > "$RELEASE_NOTES_FILE"
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "Date: $(date +"%B %d, %Y")" >> "$RELEASE_NOTES_FILE"
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "## Overview" >> "$RELEASE_NOTES_FILE"
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "This is the final v1.1.0 release of the STM32 IoT Virtual Development Environment." >> "$RELEASE_NOTES_FILE"
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "## Features and Enhancements" >> "$RELEASE_NOTES_FILE"
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "- Complete GDB integration with MicroPython debugging support" >> "$RELEASE_NOTES_FILE"
    echo "- Enhanced exception handling and visualization" >> "$RELEASE_NOTES_FILE"
    echo "- Custom UART driver optimized for QEMU" >> "$RELEASE_NOTES_FILE"
    echo "- Comprehensive unit testing framework" >> "$RELEASE_NOTES_FILE"
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "## Bug Fixes" >> "$RELEASE_NOTES_FILE"
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "- Fixed issues with GDB integration" >> "$RELEASE_NOTES_FILE"
    echo "- Improved error handling in UART driver" >> "$RELEASE_NOTES_FILE"
    echo "- Enhanced stability of QEMU integration" >> "$RELEASE_NOTES_FILE"
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "## Documentation" >> "$RELEASE_NOTES_FILE"
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "- Comprehensive documentation for all features" >> "$RELEASE_NOTES_FILE"
    echo "- Updated installation and usage guides" >> "$RELEASE_NOTES_FILE"
    echo "- Enhanced troubleshooting information" >> "$RELEASE_NOTES_FILE"
    success "Created basic release notes: $RELEASE_NOTES_FILE"
fi

echo ""
echo "Please edit the release notes file to add more details: $RELEASE_NOTES_FILE"
read -p "Press Enter to continue..."

# Run tests
section "Running tests"
echo "Running tests to ensure everything is working correctly..."

if [ -d "$TESTS_DIR" ]; then
    # Run basic tests
    echo "Running basic tests..."
    if python -m unittest discover -s "$TESTS_DIR" -p "test_*.py"; then
        success "Basic tests passed"
    else
        error "Basic tests failed"
        read -p "Press Enter to continue anyway or Ctrl+C to cancel..."
    fi
    
    # Run UART tests
    echo "Running UART tests..."
    if bash "$TESTS_DIR/test_uart.sh"; then
        success "UART tests passed"
    else
        error "UART tests failed"
        read -p "Press Enter to continue anyway or Ctrl+C to cancel..."
    fi
    
    # Run GDB tests
    echo "Running GDB tests..."
    if bash "$TESTS_DIR/test_gdb.sh"; then
        success "GDB tests passed"
    else
        error "GDB tests failed"
        read -p "Press Enter to continue anyway or Ctrl+C to cancel..."
    fi
else
    warning "Tests directory not found: $TESTS_DIR"
    read -p "Press Enter to continue anyway or Ctrl+C to cancel..."
fi

# Prepare for tagging
section "Preparing for tagging"
echo "Committing version changes..."

git add "$CURRENT_VERSION_FILE" "$VERSION_MAPPING_FILE" "$README_FILE" "$RELEASE_NOTES_FILE"
git commit -m "Prepare for v1.1.0 final release"

success "Changes committed"

echo ""
echo "To create the release tag, run:"
echo "git tag -a $NEW_SEMANTIC_VERSION -m \"Release $NEW_SEMANTIC_VERSION\""
echo "git push origin $NEW_SEMANTIC_VERSION"

# Final message
section "Release preparation complete"
echo "The v1.1.0 release has been prepared. Here's what was done:"
echo "1. Updated version files to $NEW_DATE_VERSION ($NEW_SEMANTIC_VERSION)"
echo "2. Created release notes: $RELEASE_NOTES_FILE"
echo "3. Ran tests to ensure everything is working correctly"
echo "4. Committed changes to prepare for tagging"
echo ""
echo "Next steps:"
echo "1. Review and edit the release notes: $RELEASE_NOTES_FILE"
echo "2. Create the release tag"
echo "3. Push the tag to the remote repository"
echo "4. Create a GitHub release"
echo ""
echo "Thank you for using the release preparation script!" 