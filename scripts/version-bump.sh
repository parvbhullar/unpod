#!/bin/bash

# Version Bump Script for Unpod Desktop Application
# Synchronizes version across package.json, tauri.conf.json, and Cargo.toml
# Usage: ./scripts/version-bump.sh <major|minor|patch|x.y.z>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# File paths
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_JSON="$ROOT_DIR/package.json"
TAURI_CONF="$ROOT_DIR/apps/unpod-tauri/src-tauri/tauri.conf.json"
CARGO_TOML="$ROOT_DIR/apps/unpod-tauri/src-tauri/Cargo.toml"

# Print with color
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get current version from package.json
get_current_version() {
    node -p "require('$PACKAGE_JSON').version"
}

# Parse version string into major, minor, patch
parse_version() {
    local version=$1
    IFS='.' read -r -a parts <<< "$version"
    MAJOR=${parts[0]}
    MINOR=${parts[1]}
    PATCH=${parts[2]}
}

# Calculate new version based on bump type
calculate_new_version() {
    local bump_type=$1
    local current=$2

    parse_version "$current"

    case $bump_type in
        major)
            echo "$((MAJOR + 1)).0.0"
            ;;
        minor)
            echo "$MAJOR.$((MINOR + 1)).0"
            ;;
        patch)
            echo "$MAJOR.$MINOR.$((PATCH + 1))"
            ;;
        *)
            # Assume it's a direct version number
            if [[ $bump_type =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                echo "$bump_type"
            else
                print_error "Invalid version format: $bump_type"
                print_info "Use: major, minor, patch, or x.y.z format"
                exit 1
            fi
            ;;
    esac
}

# Update package.json
update_package_json() {
    local new_version=$1
    print_info "Updating package.json..."

    # Use node to update JSON properly
    node -e "
        const fs = require('fs');
        const pkg = require('$PACKAGE_JSON');
        pkg.version = '$new_version';
        fs.writeFileSync('$PACKAGE_JSON', JSON.stringify(pkg, null, 2) + '\n');
    "
    print_success "package.json updated to $new_version"
}

# Update tauri.conf.json
update_tauri_conf() {
    local new_version=$1
    print_info "Updating tauri.conf.json..."

    node -e "
        const fs = require('fs');
        const conf = require('$TAURI_CONF');
        conf.version = '$new_version';
        fs.writeFileSync('$TAURI_CONF', JSON.stringify(conf, null, 2) + '\n');
    "
    print_success "tauri.conf.json updated to $new_version"
}

# Update Cargo.toml
update_cargo_toml() {
    local new_version=$1
    print_info "Updating Cargo.toml..."

    # Use sed to update version in Cargo.toml (first occurrence under [package])
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed
        sed -i '' "s/^version = \"[0-9]*\.[0-9]*\.[0-9]*\"/version = \"$new_version\"/" "$CARGO_TOML"
    else
        # Linux sed
        sed -i "s/^version = \"[0-9]*\.[0-9]*\.[0-9]*\"/version = \"$new_version\"/" "$CARGO_TOML"
    fi
    print_success "Cargo.toml updated to $new_version"
}

# Validate all versions are in sync
validate_versions() {
    local pkg_version=$(node -p "require('$PACKAGE_JSON').version")
    local tauri_version=$(node -p "require('$TAURI_CONF').version")
    local cargo_version=$(grep '^version' "$CARGO_TOML" | head -1 | sed 's/version = "\(.*\)"/\1/')

    if [[ "$pkg_version" == "$tauri_version" && "$pkg_version" == "$cargo_version" ]]; then
        print_success "All versions synchronized: $pkg_version"
        return 0
    else
        print_error "Version mismatch detected!"
        print_info "  package.json:    $pkg_version"
        print_info "  tauri.conf.json: $tauri_version"
        print_info "  Cargo.toml:      $cargo_version"
        return 1
    fi
}

# Create git tag
create_git_tag() {
    local version=$1
    local tag="v$version"

    print_info "Creating git tag: $tag"

    # Check if tag already exists
    if git rev-parse "$tag" >/dev/null 2>&1; then
        print_warning "Tag $tag already exists. Skipping tag creation."
        return 0
    fi

    git add "$PACKAGE_JSON" "$TAURI_CONF" "$CARGO_TOML"
    git commit -m "chore(release): bump version to $version"
    git tag -a "$tag" -m "Release $tag"

    print_success "Created git tag: $tag"
    print_info "Push with: git push origin $tag"
}

# Show usage
show_usage() {
    echo ""
    echo "Unpod Desktop Version Bump Script"
    echo "=================================="
    echo ""
    echo "Usage: $0 <bump_type> [--tag] [--push]"
    echo ""
    echo "Arguments:"
    echo "  bump_type    One of: major, minor, patch, or a specific version (x.y.z)"
    echo ""
    echo "Options:"
    echo "  --tag        Create a git tag after version bump"
    echo "  --push       Push the tag to remote (implies --tag)"
    echo "  --dry-run    Show what would be done without making changes"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 patch                  # 2.0.0 -> 2.0.1"
    echo "  $0 minor                  # 2.0.0 -> 2.1.0"
    echo "  $0 major                  # 2.0.0 -> 3.0.0"
    echo "  $0 2.1.0                  # Set exact version"
    echo "  $0 patch --tag            # Bump and create git tag"
    echo "  $0 minor --push           # Bump, tag, and push"
    echo ""
}

# Main function
main() {
    local bump_type=""
    local create_tag=false
    local push_tag=false
    local dry_run=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --tag)
                create_tag=true
                shift
                ;;
            --push)
                create_tag=true
                push_tag=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                if [[ -z "$bump_type" ]]; then
                    bump_type=$1
                else
                    print_error "Unknown argument: $1"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # Validate bump type
    if [[ -z "$bump_type" ]]; then
        print_error "Missing bump type argument"
        show_usage
        exit 1
    fi

    # Get current and new versions
    local current_version=$(get_current_version)
    local new_version=$(calculate_new_version "$bump_type" "$current_version")

    echo ""
    echo "======================================"
    echo " Unpod Desktop Version Bump"
    echo "======================================"
    echo ""
    print_info "Current version: $current_version"
    print_info "New version:     $new_version"
    echo ""

    if [[ "$dry_run" == true ]]; then
        print_warning "DRY RUN - No changes will be made"
        echo ""
        print_info "Would update:"
        print_info "  - package.json"
        print_info "  - apps/unpod-tauri/src-tauri/tauri.conf.json"
        print_info "  - apps/unpod-tauri/src-tauri/Cargo.toml"
        if [[ "$create_tag" == true ]]; then
            print_info "  - Would create git tag: v$new_version"
        fi
        if [[ "$push_tag" == true ]]; then
            print_info "  - Would push tag to remote"
        fi
        exit 0
    fi

    # Update all files
    update_package_json "$new_version"
    update_tauri_conf "$new_version"
    update_cargo_toml "$new_version"

    echo ""

    # Validate
    if ! validate_versions; then
        print_error "Version synchronization failed!"
        exit 1
    fi

    # Create git tag if requested
    if [[ "$create_tag" == true ]]; then
        echo ""
        create_git_tag "$new_version"
    fi

    # Push tag if requested
    if [[ "$push_tag" == true ]]; then
        local tag="v$new_version"
        print_info "Pushing tag $tag to remote..."
        git push origin "$tag"
        print_success "Tag pushed to remote"
    fi

    echo ""
    echo "======================================"
    print_success "Version bump complete!"
    echo "======================================"
    echo ""

    if [[ "$create_tag" == false ]]; then
        print_info "Next steps:"
        echo "  1. Review changes: git diff"
        echo "  2. Commit: git add -A && git commit -m 'chore(release): bump version to $new_version'"
        echo "  3. Tag: git tag -a v$new_version -m 'Release v$new_version'"
        echo "  4. Push: git push origin v$new_version"
        echo ""
        print_info "Or run: $0 $bump_type --push"
    fi
}

# Run main
main "$@"
