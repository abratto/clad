#!/usr/bin/env python3
"""
rename_sync.py — rename a sync and its whole tail in one step.

Why this exists:
  Renaming a sync is more than `mv`: the `sync <Name>` header, every
  `<Name>.sync.md` reference in the feature's cards / derivation maps / trace /
  README, the Java `rule("<Name>")` (and, in a class-per-rule profile, the class
  and file), and the `<Name>Test` class all move with it. Doing this by hand
  burned most of the route-scoped-pinned-names change. This does it, then runs
  `verify_reference_integrity.py` and prints the re-approval the rename needs.

Default is a dry run; pass `--write` to apply. A sync rename invalidates
**Gate 2** (Stage 03), and the Java rule/test rename sits in 04e (no gate).

Usage:
  python3 rename_sync.py --feature features/UC-XX-<slug> \
      --from <OldName> --to <NewName> \
      [--sync-impl-dir <dir>] [--test-source-root <dir>] [--write]
"""

import argparse
import os
import re
import subprocess
import sys

SKIP_DIRS = {"_changes", "__pycache__", "target", ".git"}


def replace_in(path, pairs):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    new = text
    for old, rep in pairs:
        new = new.replace(old, rep)
    if new != text:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(new)
        return True
    return False


def walk(directory, suffixes):
    for dirpath, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            if name.endswith(suffixes):
                yield os.path.join(dirpath, name)


def rename_spec(feature_root, old, new, write):
    out = os.path.join(feature_root, "stages/03_syncs/output")
    src = os.path.join(out, f"{old}.sync.md")
    dst = os.path.join(out, f"{new}.sync.md")
    if not os.path.isfile(src):
        print(f"FAIL  no sync spec at {src}")
        return False
    print(f"  rename {os.path.basename(src)} -> {os.path.basename(dst)}")
    if write:
        os.rename(src, dst)
        replace_in(dst, [(f"sync {old}", f"sync {new}")])
    return True


def rename_doc_refs(feature_root, old, new, write):
    for path in walk(feature_root, (".md", ".feature")):
        if write:
            if replace_in(path, [(f"{old}.sync.md", f"{new}.sync.md")]):
                print(f"  update {os.path.relpath(path, feature_root)}")


def rename_java(sync_impl_dir, old, new, write):
    if not sync_impl_dir or not os.path.isdir(sync_impl_dir):
        return
    pairs = [(f'rule("{old}")', f'rule("{new}")'),
             (f'SyncRule.of("{old}"', f'SyncRule.of("{new}"'),
             (f'SyncRule.ofJoin("{old}"', f'SyncRule.ofJoin("{new}"')]
    for path in walk(sync_impl_dir, (".java",)):
        if write and replace_in(path, pairs):
            print(f"  update {os.path.basename(path)} (rule name)")
    # class-per-rule profile: rename the class file + declaration
    for path in walk(sync_impl_dir, (".java",)):
        if os.path.basename(path) == f"{old}.java":
            dst = os.path.join(os.path.dirname(path), f"{new}.java")
            print(f"  rename {os.path.basename(path)} -> {os.path.basename(dst)}")
            if write:
                replace_in(path, [(f"class {old}", f"class {new}")])
                os.rename(path, dst)


def rename_test(test_root, old, new, write):
    if not test_root or not os.path.isdir(test_root):
        return
    for path in walk(test_root, (".java",)):
        if os.path.basename(path) == f"{old}Test.java":
            dst = os.path.join(os.path.dirname(path), f"{new}Test.java")
            print(f"  rename {os.path.basename(path)} -> {os.path.basename(dst)}")
            if write:
                replace_in(path, [(f"{old}Test", f"{new}Test"),
                                  (f"{{@code {old}}}", f"{{@code {new}}}")])
                os.rename(path, dst)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename a sync and its tail")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--from", dest="old", required=True)
    parser.add_argument("--to", dest="new", required=True)
    parser.add_argument("--sync-impl-dir", default="")
    parser.add_argument("--test-source-root", default="")
    parser.add_argument("--write", action="store_true",
                        help="Apply (default is a dry run)")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    print(f"{'WRITE' if args.write else 'DRY RUN'}  rename sync "
          f"{args.old} -> {args.new}")
    if not rename_spec(feature_root, args.old, args.new, args.write):
        return 1
    rename_doc_refs(feature_root, args.old, args.new, args.write)
    rename_java(args.sync_impl_dir, args.old, args.new, args.write)
    rename_test(args.test_source_root, args.old, args.new, args.write)

    if args.write:
        checker = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "verify_reference_integrity.py")
        result = subprocess.run(
            [sys.executable, checker, "--features-dir",
             os.path.dirname(feature_root)],
            capture_output=True, text=True)
        print(result.stdout.strip() or result.stderr.strip())

    print("Re-approve Gate 2 (Stage 03) — the sync rename invalidates it; "
          "the Java/test rename (04e) needs no gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
