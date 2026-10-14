#!/usr/bin/env python3
"""
create_consent.py — scaffold a remodel consent receipt (R22).

A `remodel` proposal needs a consent receipt from every feature on the concept's
canonical history (minus the proposer), at
`features/_system/concepts/_remodel-consent/<Concept>-<feature>.md`. Promotion
refuses without it (`concept_remodel.missing_consent`). This writes the stub; the
reviewer fills in the reason and the sign-off.

Usage:
  python3 create_consent.py --feature features/UC-06-x \
                            --concept DrinkLogging \
                            --consenting UC-04-log-drink \
                            --change features/UC-06-x/_changes/<slug>.md
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concept_remodel as cr  # noqa: E402
import promote_concepts as pc  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a remodel consent receipt")
    parser.add_argument("--feature", required=True,
                        help="The proposing feature root")
    parser.add_argument("--concept", required=True)
    parser.add_argument("--consenting", required=True,
                        help="The historical feature whose sign-off is recorded")
    parser.add_argument("--change", default="",
                        help="The _changes/<slug> this consent is for")
    args = parser.parse_args()

    feature = os.path.abspath(args.feature)
    corpus = pc.corpus_dir(feature)
    if not os.path.isdir(corpus):
        print(f"FAIL  no canonical corpus at {corpus}")
        return 1

    directory = cr.consent_dir(corpus)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{args.concept}-{args.consenting}.md")
    if os.path.exists(path):
        print(f"SKIP  consent receipt already exists: {path}")
        return 0

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(
            f"# Remodel consent — `{args.concept}`\n\n"
            f"- **Concept:** `{args.concept}`\n"
            f"- **Consenting feature:** `{args.consenting}`\n"
            f"- **Proposer:** `{pc.feature_slug(feature)}`\n"
            + (f"- **Proposal:** `{args.change}`\n" if args.change else "")
            + "- **Consent:** `approved`\n\n"
            f"`{args.consenting}` consents to the non-additive remodel of "
            f"`{args.concept}` (see the proposal's `## Migration notes`).\n")
    print(f"WROTE {path}")
    print("  Fill in the reason and confirm the sign-off before promoting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
