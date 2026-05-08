#!/usr/bin/env bash
# Tracking-hygiene check: enforce the ROADMAP.md conventions documented in
# methodology/overlays/TRACKING.md. Optional overlay — skipped if ROADMAP.md
# is absent.
#
# Rules enforced:
#   1. At most one phase row has status `doing`.
#   2. A "Resume point" section exists.
#   3. The "Last updated:" line under "Resume point" is no older than
#      ROADMAP_MAX_AGE_DAYS (default 60).
#
# Emits GitHub-style ::error annotations on failure.

set -euo pipefail

ROADMAP="${ROADMAP_PATH:-ROADMAP.md}"
MAX_AGE_DAYS="${ROADMAP_MAX_AGE_DAYS:-60}"

if [ ! -f "$ROADMAP" ]; then
  echo "Tracking overlay not in use ($ROADMAP not present); skipping."
  exit 0
fi

violations=0

# --- Rule 1: at most one `doing` row ----------------------------------------
# Match table rows that contain a pipe-delimited cell whose trimmed value is
# exactly "doing" (case-insensitive).
doing_count=$(awk -F'|' '
  /^\|/ {
    for (i = 1; i <= NF; i++) {
      cell = $i
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", cell)
      if (tolower(cell) == "doing") { print; next }
    }
  }
' "$ROADMAP" | wc -l | tr -d ' ')

if [ "$doing_count" -gt 1 ]; then
  echo "::error file=$ROADMAP::Tracking violation: $doing_count phase rows have status 'doing' (expected at most 1). See methodology/overlays/TRACKING.md."
  violations=$((violations + 1))
fi

# --- Rule 2: Resume point section exists ------------------------------------
if ! grep -qE '^##[[:space:]]+Resume point' "$ROADMAP"; then
  echo "::error file=$ROADMAP::Tracking violation: missing '## Resume point' section. See methodology/overlays/TRACKING.md."
  violations=$((violations + 1))
fi

# --- Rule 3: Last updated date is recent ------------------------------------
last_updated=$(grep -E '\*\*Last updated:\*\*' "$ROADMAP" 2>/dev/null | head -1 | sed -E 's/.*\*\*Last updated:\*\*[[:space:]]*([0-9]{4}-[0-9]{2}-[0-9]{2}).*/\1/' || true)

if [ -z "$last_updated" ]; then
  echo "::error file=$ROADMAP::Tracking violation: missing or unparseable '**Last updated:** YYYY-MM-DD' line under Resume point."
  violations=$((violations + 1))
else
  # Portable date diff: works on GNU date (Linux/CI) and BSD date (macOS).
  if date --version >/dev/null 2>&1; then
    last_epoch=$(date -d "$last_updated" +%s)
  else
    last_epoch=$(date -j -f "%Y-%m-%d" "$last_updated" +%s)
  fi
  now_epoch=$(date +%s)
  age_days=$(( (now_epoch - last_epoch) / 86400 ))
  if [ "$age_days" -gt "$MAX_AGE_DAYS" ]; then
    echo "::error file=$ROADMAP::Tracking violation: Resume point is $age_days days old (threshold $MAX_AGE_DAYS). Update the '**Last updated:**' line and the resume point fields above it."
    violations=$((violations + 1))
  fi
fi

if [ "$violations" -gt 0 ]; then
  echo ""
  echo "Tracking-hygiene check failed with $violations violation(s)."
  exit 1
fi

echo "Tracking-hygiene check passed: 1 active phase, resume point present and current."
