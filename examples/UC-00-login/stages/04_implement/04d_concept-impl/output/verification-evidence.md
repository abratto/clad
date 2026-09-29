# Verification evidence — UC-00 concept implementation

- **Stage:** 04d (concept implementation)
- **Test command:** `python3 quality-gate/verify_artefacts.py && mvn test -f reference-impl/pom.xml -pl java-legible -am`
- **Result:** pass — concept unit tests green
  (`UserNamingLookupByUsernameTest`, `PasswordAuthCheckTest`; `Session.grant`
  covered through the flow/sync tests).
- **Contract-outcome coverage:** every outcome in
  [`../04b_contract/output/`](../04b_contract/output/) has a row in
  [`concept-test-derivation.md`](concept-test-derivation.md).
- **Mutation score:** reported by `verify_mutation_score.py` when the
  profile configures `mutation.command`; this worked example sets none, so
  the check skips and effectiveness rests on contract-outcome coverage and
  the field assertions (R14/R16).
