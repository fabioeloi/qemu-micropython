#!/bin/bash
# Prepare the final v1.1.0 release
set -e

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CURRENT_VERSION_FILE="$PROJECT_DIR/CURRENT_VERSION"
VERSION_MAPPING_FILE="$PROJECT_DIR/VERSION_MAPPING.md"
README_FILE="$PROJECT_DIR/README.md"
ROADMAP_FILE="$PROJECT_DIR/ROADMAP_STATUS.md"
RELEASE_NOTES_TEMPLATE="$PROJECT_DIR/docs/release_notes/v1.1.0_template.md"
RELEASE_NOTES_FILE="$PROJECT_DIR/docs/release_notes/v1.1.0.md"
FINAL_VERSION="v1.1.0"
DATE_VERSION="v$(date +%Y.%m.%d).18"

echo "Preparing final release $FINAL_VERSION ($DATE_VERSION)..."

# Check if all necessary files exist
for file in "$CURRENT_VERSION_FILE" "$VERSION_MAPPING_FILE" "$README_FILE" "$ROADMAP_FILE" "$RELEASE_NOTES_TEMPLATE"; do
    if [ ! -f "$file" ]; then
        echo "Error: File $file not found"
        exit 1
    fi
done

# Update CURRENT_VERSION file
echo "Updating CURRENT_VERSION file..."
echo "$DATE_VERSION" > "$CURRENT_VERSION_FILE"
echo "$FINAL_VERSION" >> "$CURRENT_VERSION_FILE"

# Update VERSION_MAPPING.md
echo "Updating VERSION_MAPPING.md..."
sed -i '' "s/| TBD               | $FINAL_VERSION/| $DATE_VERSION        | $FINAL_VERSION/" "$VERSION_MAPPING_FILE"

# Update README.md
echo "Updating README.md..."
sed -i '' "s/^**Current Release:.*$/**Current Release:** $DATE_VERSION ($FINAL_VERSION)/" "$README_FILE"
sed -i '' "s/~99% complete/100% complete/" "$README_FILE"

# Update ROADMAP_STATUS.md
echo "Updating ROADMAP_STATUS.md..."
sed -i '' "s/In Progress | v2025.03.04.17 | 99%/Completed | $DATE_VERSION | 100%/" "$ROADMAP_FILE"
sed -i '' "s/In Progress | v2025.03.04.17 | 97%/Completed | $DATE_VERSION | 100%/" "$ROADMAP_FILE"
sed -i '' "s/~99% completion/100% completion/" "$ROADMAP_FILE"

# Create final release notes
echo "Creating final release notes..."
if [ -f "$RELEASE_NOTES_TEMPLATE" ]; then
    cp "$RELEASE_NOTES_TEMPLATE" "$RELEASE_NOTES_FILE"
    sed -i '' "s/v1.1.0 (Final)/$FINAL_VERSION (Final)/" "$RELEASE_NOTES_FILE"
    echo "Final release notes created at $RELEASE_NOTES_FILE"
else
    echo "Warning: Release notes template not found at $RELEASE_NOTES_TEMPLATE"
    echo "Please create the final release notes manually"
fi

# Stage changes
echo "Staging changes..."
git add "$CURRENT_VERSION_FILE" "$VERSION_MAPPING_FILE" "$README_FILE" "$ROADMAP_FILE" "$RELEASE_NOTES_FILE"

# Create commit message
echo "Creating commit message..."
COMMIT_MESSAGE="Release $FINAL_VERSION ($DATE_VERSION): Final Release

This commit marks the final release of the v1.1.0 milestone, completing the Debugging and QEMU Integration phase of the project.

Key accomplishments:
- Comprehensive GDB integration with MicroPython debugging support
- Enhanced exception handling and visualization
- Custom UART driver with simulation capabilities
- Basic semihosting integration
- Comprehensive testing framework
- Detailed documentation

All major features are now complete and documented, with the milestone at 100% completion.

Next steps will focus on the v1.2.0 milestone: IoT and Simulation Capabilities."

# Show summary
echo ""
echo "Release preparation complete. Please review the changes:"
echo ""
git diff --staged
echo ""
echo "Commit message:"
echo "$COMMIT_MESSAGE"
echo ""
echo "To complete the release process, run:"
echo "git commit -m \"$COMMIT_MESSAGE\""
echo "git tag $FINAL_VERSION"
echo "git push origin main --tags"
echo ""
echo "Then create a GitHub release with the release notes from:"
echo "$RELEASE_NOTES_FILE" 