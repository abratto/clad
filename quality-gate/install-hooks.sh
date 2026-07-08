#!/usr/bin/env bash
#
# install-hooks.sh — activate CLAD's local git hooks for this clone.
#
# CLAD ships its hooks under .githooks/ (which IS version-controlled) but git
# never runs a cloned repo's hooks automatically — .git/hooks/ is not cloned,
# by design. This one-time command points git at the tracked hooks directory:
#
#   git config core.hooksPath .githooks
#
# After running it, `git commit` will run .githooks/pre-commit, which refuses
# commits that skip a CLAD stage or leave an implementation decoupled from its
# spec. To undo:  git config --unset core.hooksPath
#
# Strongly recommended for anyone cloning CLAD as a template — it converts the
# stage-sequence rule from "enforced only if the agent runs advance.py" into
# "enforced at every commit."

set -eu

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
    echo "install-hooks: not inside a git repository." >&2
    exit 1
fi
cd "$repo_root"

if [ ! -d .githooks ]; then
    echo "install-hooks: .githooks/ not found at repo root." >&2
    exit 1
fi

chmod +x .githooks/* 2>/dev/null || true
git config core.hooksPath .githooks

echo "CLAD hooks installed: core.hooksPath -> .githooks"
echo "  pre-commit will now enforce stage sequence + iterative-change coupling."
echo "  Bypass one commit with:  git commit --no-verify"
echo "  Uninstall with:          git config --unset core.hooksPath"
