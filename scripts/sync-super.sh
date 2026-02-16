#!/usr/bin/env bash
set -euo pipefail

# Bidirectional sync between super sources and apps/super mirrors.
# Uses rsync --update to copy only newer/changed files in each direction.

# Sync pairs: "source|target"
SYNC_PAIRS=(
    "/Users/parvbhullar/Drives/Vault/Projects/Unpod/super/super_os/|/Users/parvbhullar/Drives/Vault/Projects/Unpod/unpod-os/apps/super/super/"
    "/Users/parvbhullar/Drives/Vault/Projects/Unpod/super/super_services/|/Users/parvbhullar/Drives/Vault/Projects/Unpod/unpod-os/apps/super/super_services/"
)

EXCLUDES=(
    "__pycache__"
    "*.pyc"
    ".DS_Store"
    "*.egg-info"
    ".pytest_cache"
    ".mypy_cache"
    ".ruff_cache"
)

RSYNC_OPTS=(
    --archive
    --update          # skip files newer on receiver
    --verbose
    --human-readable
    --delete          # remove files from dest if deleted in source
    --itemize-changes # show exactly what changed
)

for pattern in "${EXCLUDES[@]}"; do
    RSYNC_OPTS+=(--exclude "$pattern")
done

usage() {
    echo "Usage: $0 [push|pull|sync|status]"
    echo ""
    echo "  push    Copy changes from apps/super -> sources"
    echo "  pull    Copy changes from sources -> apps/super"
    echo "  sync    Bidirectional: push then pull (newer file wins)"
    echo "  status  Dry-run diff in both directions (no changes made)"
    exit 1
}

ensure_dirs() {
    for pair in "${SYNC_PAIRS[@]}"; do
        local src="${pair%%|*}"
        local tgt="${pair##*|}"
        if [[ ! -d "$src" ]]; then
            echo "Error: source directory not found: $src"
            exit 1
        fi
        mkdir -p "$tgt"
    done
}

do_push() {
    for pair in "${SYNC_PAIRS[@]}"; do
        local src="${pair%%|*}"
        local tgt="${pair##*|}"
        echo "=== PUSH: $tgt -> $src ==="
        rsync "${RSYNC_OPTS[@]}" "$tgt" "$src"
        echo ""
    done
    echo "Push complete."
}

do_pull() {
    for pair in "${SYNC_PAIRS[@]}"; do
        local src="${pair%%|*}"
        local tgt="${pair##*|}"
        echo "=== PULL: $src -> $tgt ==="
        rsync "${RSYNC_OPTS[@]}" "$src" "$tgt"
        echo ""
    done
    echo "Pull complete."
}

do_sync() {
    echo "=== SYNC: bidirectional (newer file wins) ==="
    echo ""
    for pair in "${SYNC_PAIRS[@]}"; do
        local src="${pair%%|*}"
        local tgt="${pair##*|}"
        echo "--- Push: $tgt -> $src ---"
        rsync "${RSYNC_OPTS[@]}" "$tgt" "$src" 2>/dev/null || true
        echo ""
        echo "--- Pull: $src -> $tgt ---"
        rsync "${RSYNC_OPTS[@]}" "$src" "$tgt"
        echo ""
    done
    echo "Sync complete."
}

do_status() {
    echo "=== STATUS: dry-run diff (no changes made) ==="
    echo ""
    for pair in "${SYNC_PAIRS[@]}"; do
        local src="${pair%%|*}"
        local tgt="${pair##*|}"
        echo "--- Would push: $tgt -> $src ---"
        rsync "${RSYNC_OPTS[@]}" --dry-run "$tgt" "$src" 2>/dev/null || true
        echo ""
        echo "--- Would pull: $src -> $tgt ---"
        rsync "${RSYNC_OPTS[@]}" --dry-run "$src" "$tgt"
        echo ""
    done
    echo "Status complete. No files were changed."
}

ensure_dirs

case "${1:-}" in
    push)   do_push   ;;
    pull)   do_pull   ;;
    sync)   do_sync   ;;
    status) do_status ;;
    *)      usage     ;;
esac
