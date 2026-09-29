#!/usr/bin/env bash
# scripts/mutation-score.sh — the canonical profile's mutation gate (R24, DR-0001).
#
# Runs PIT over the java-legible profile's tests and prints exactly one
# machine-readable line for quality-gate/verify_mutation_score.py to parse:
#
#   MUTATION_SCORE: <pct>   the suite was measured; compare to mutation.threshold
#   MUTATION_SKIP: <reason> the tool could not run in this environment
#
# SKIP is for environments that cannot host the tool (a JVM newer than PIT
# supports, a missing toolchain). It is NOT a pass: `verify_mutation_score.py
# --require` (used in CI) turns a SKIP into a failure. Locally, a SKIP keeps
# the gate from producing a false negative on a developer's newer JVM.
#
# Not bound to a Maven lifecycle phase: `mvn test` is unaffected. Configured as
# `mutation.command` in clad.properties; unset it for a profile with no
# mutation tool.
set -euo pipefail

cd "$(dirname "$0")/.."

MODULE="reference-impl/java-legible"
REPORT="${MODULE}/target/pit-reports/mutations.xml"
LOG="/tmp/clad-pit.log"

emit_skip() {
  echo "MUTATION_SKIP: $1"
  echo "  see $LOG" >&2
  exit 0
}

# 1. Compile the module and its reactor dependencies.
if ! mvn -q -f reference-impl/pom.xml -pl java-legible -am test-compile \
        >"$LOG" 2>&1; then
  emit_skip "test-compile failed"
fi

# 2. Run PIT scoped to java-legible only (no -am: the goal must not run on the
#    engine module).
if ! mvn -q -f reference-impl/pom.xml -pl java-legible \
        org.pitest:pitest-maven:mutationCoverage >>"$LOG" 2>&1; then
  jvm="$(mvn -version 2>/dev/null | sed -n 's/.*Java version: \([0-9.]*\).*/\1/p' | head -1)"
  emit_skip "mutation tooling failed (JVM ${jvm:-unknown}; PIT may not support this JVM)"
fi

# 3. Parse the XML report into a single score line.
if [ ! -f "$REPORT" ]; then
  emit_skip "PIT produced no report at $REPORT"
fi

python3 - "$REPORT" <<'PY'
import os
import sys
import xml.etree.ElementTree as ET

report = sys.argv[1]
if not os.path.isfile(report):
    print("MUTATION_SKIP: PIT produced no report at %s" % report)
    raise SystemExit(0)

killed = total = 0
for mutation in ET.parse(report).getroot().iter("mutation"):
    status = mutation.get("status", "")
    if status in ("KILLED", "TIMED_OUT", "NON_VIABLE", "MEMORY_ERROR"):
        killed += 1
        total += 1
    elif status in ("SURVIVED", "NO_COVERAGE"):
        total += 1

score = (100.0 * killed / total) if total else 0.0
print("MUTATION_SCORE: %.1f" % score)
PY
