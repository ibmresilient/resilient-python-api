#!/bin/bash
set -euo pipefail

## ----------------------------------------------------------------------------
## create_version_tag.sh
## ----------------------------------------------------------------------------
## Description:
##   Reads the version from resilient/pyproject.toml and creates a git tag if
##   it doesn't already exist. This ensures version tags are synchronized with
##   the explicit version variables in pyproject.toml files.
##
## Usage:
##   ./create_version_tag.sh [--push]
##
## Options:
##   --push    Push the tag to remote after creating it
## ----------------------------------------------------------------------------

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Parse arguments
SHOULD_PUSH=false
if [[ "${1:-}" == "--push" ]]; then
    SHOULD_PUSH=true
fi

# Function to extract version from pyproject.toml
get_version_from_pyproject() {
    local pyproject_path="$1"

    if [[ ! -f "$pyproject_path" ]]; then
        echo "ERROR: pyproject.toml not found at: $pyproject_path" >&2
        return 1
    fi

    # Extract the static `version = "..."` line under [project]
    # Replacing \s with [[:space:]] is POSIX-standard and works on both BSD (macOS) and GNU (Linux) awk
    local version
    version=$(awk -F'"' '/^version[[:space:]]*=/{print $2; exit}' "$pyproject_path")

    if [[ -z "$version" ]]; then
        echo "ERROR: No version found in $pyproject_path" >&2
        return 1
    fi

    echo "$version"
}

# Function to check if tag exists
tag_exists() {
    local tag="$1"
    git rev-parse "$tag" >/dev/null 2>&1
}

# Function to create tag
create_tag() {
    local tag="$1"
    local version="$2"
    
    echo "Creating tag: $tag"
    git tag -a "$tag" -m "Release version $version"
    
    if [[ "$SHOULD_PUSH" == true ]]; then
        echo "Pushing tag: $tag"
        git push origin "$tag"
    fi
}

# Main execution
main() {
    cd "$REPO_ROOT"
    
    # Get version from resilient/pyproject.toml
    local version
    version=$(get_version_from_pyproject "${REPO_ROOT}/resilient/pyproject.toml")

    if [[ -z "$version" ]]; then
        echo "ERROR: Could not determine version from resilient/pyproject.toml" >&2
        exit 1
    fi

    echo "Version from pyproject.toml: $version"
    
    # Create tag name with 'v' prefix
    local tag="v${version}"
    
    # Check if tag already exists
    if tag_exists "$tag"; then
        echo "Tag $tag already exists. Skipping creation."
        exit 0
    fi
    
    # Create the tag
    create_tag "$tag" "$version"
    
    echo "Successfully created tag: $tag"
    
    if [[ "$SHOULD_PUSH" == false ]]; then
        echo "Note: Tag was created locally. Use --push to push to remote."
    fi
}

# Run main function
main "$@"

# Made with Bob
