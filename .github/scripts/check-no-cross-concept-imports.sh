#!/usr/bin/env bash
# R1 enforcement: no Java import crosses concept package boundaries.
#
# A "concept package" is any directory under reference-impl/<profile>/src/main/java
# whose path matches **/concepts/<X>/. An import statement in a file
# under <X>/ is illegal if it references **/concepts/<Y>/ where Y != X.
#
# Exits non-zero on the first violation. Prints all violations.

set -euo pipefail

violations=0

# Find every Java source file under any concepts/<X>/ subtree.
files=()
while IFS= read -r -d '' f; do
  files+=("$f")
done < <(find reference-impl -type f -name '*.java' -path '*/concepts/*' -print0 2>/dev/null || true)

if [ ${#files[@]} -eq 0 ]; then
  echo "No Java concept files found under reference-impl/. Skipping R1 check."
  exit 0
fi

for f in "${files[@]}"; do
  # Extract this file's concept name: the segment after /concepts/.
  own_concept=$(echo "$f" | sed -E 's|.*/concepts/([^/]+)/.*|\1|')

  # Look for imports of any sibling concept.
  # Match: import ...concepts.<Y>... where Y != own_concept
  while IFS= read -r line; do
    other=$(echo "$line" | sed -E 's|.*\.concepts\.([^.;]+).*|\1|')
    if [ "$other" != "$own_concept" ]; then
      echo "::error file=$f::R1 violation: imports concept '$other' from concept '$own_concept' — $line"
      violations=$((violations + 1))
    fi
  done < <(grep -E '^\s*import\s+[a-zA-Z0-9_.]+\.concepts\.[a-zA-Z0-9_]+' "$f" || true)
done

if [ "$violations" -gt 0 ]; then
  echo ""
  echo "Found $violations R1 violation(s). See methodology/implementation/RULES.md."
  exit 1
fi

echo "R1 check passed: no cross-concept imports found in $(echo ${#files[@]}) Java file(s)."
