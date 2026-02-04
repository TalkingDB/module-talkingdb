#!/bin/bash

VERSION_FILE="version.txt"
DEFAULT_VERSION="0.0.0"

# Ensure that git is configured
git_config() {
    git config --global user.email "mayank.g@smarter.codes"
    git config --global user.name "immkg"
}

if [ ! -f "$VERSION_FILE" ]; then
    echo "$DEFAULT_VERSION" > "$VERSION_FILE"
fi

current_version=$(cat "$VERSION_FILE")
IFS='.' read -r -a version_parts <<< "$current_version"

bump_major() {
    ((version_parts[0]++))
    version_parts[1]=0
    version_parts[2]=0
}

bump_minor() {
    ((version_parts[1]++))
    version_parts[2]=0
}

bump_patch() {
    ((version_parts[2]++))
}

commit_changes() {
    git add "$VERSION_FILE"
    git commit -m "Bump version to $new_version [skip ci]"
    git push origin HEAD
}

case "$1" in
    major)
        bump_major
        ;;
    minor)
        bump_minor
        ;;
    patch)
        bump_patch
        ;;
    *)
        echo "Usage: $0 {major|minor|patch}"
        exit 1
        ;;
esac

new_version="${version_parts[0]}.${version_parts[1]}.${version_parts[2]}"
echo "$new_version" > "$VERSION_FILE"
echo "Version updated to $new_version"

# Configure Git and commit changes
git_config
commit_changes
