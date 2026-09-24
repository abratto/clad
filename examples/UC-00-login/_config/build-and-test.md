# Build-and-test command (UC-00-login)

`mvn -f reference-impl/pom.xml test -pl java-legible`

The canonical test command in `clad.properties` (`test.command`) runs
`verify_artefacts.py` first, then the profile test framework. Prefer that
full command for executed evidence (R19).
