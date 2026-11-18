#!/usr/bin/env python3
"""Halpin-derived conformance tests for the supported Rmap subset.

The contract itself lives in `methodology/architecture/RMAP_CONFORMANCE.md`.
Each test names the rule it pins so a future change to the subset has to
update the contract deliberately.
"""

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import artifact_parsers as ap  # noqa: E402
import generate_data_model as gdm  # noqa: E402
import rmap  # noqa: E402
import verify_data_model as vdm  # noqa: E402


def _derive(concept, body, **kwargs):
    return rmap.derive_model(
        concept, "## Conceptual model\n\n```\n" + body.strip() + "\n```\n",
        **kwargs)


def _machine(body):
    return ap.parse_machine_model(
        "## Conceptual model\n\n```\n" + body.strip() + "\n```\n")


class HalpinMappingTests(unittest.TestCase):

    def test_simple_key_facts_group_on_the_subject_table(self):
        model = _derive("Profiling", """
object-type UserId identified-by UserId
fact email : UserId -> Email -- mandatory, unique
fact displayName : UserId -> Name -- optional
""")
        self.assertEqual([table.table for table in model.tables], ["profiling"])
        table = model.tables[0]
        self.assertEqual(table.primary_key, ["user_id"])
        self.assertTrue(table.column_for("email").mandatory)
        self.assertTrue(table.column_for("email").unique)
        self.assertFalse(table.column_for("displayName").mandatory)

    def test_composite_key_fact_gets_its_own_table(self):
        model = _derive("Registry", """
object-type Member identified-by Member
object-type Copy identified-by Copy
fact priority : ( Member, Copy ) -> Int -- optional
""")
        table = next(table for table in model.tables
                     if len(table.primary_key) == 2)
        self.assertEqual(table.primary_key, ["member", "copy"])
        self.assertFalse(table.column_for("priority").mandatory)


class AbsorptionConformanceTests(unittest.TestCase):

    BODY = """
object-type Party identified-by Party
object-type Employer identified-by Employer
fact partyName : Party -> PartyName -- mandatory
fact vatNumber : Employer -> VatNumber -- mandatory
fact payrollRef : Employer -> PayrollRef -- optional
Employer is a Party -- mapping: absorb
"""

    def test_mandatory_subtype_fact_is_nullable_on_the_supertype(self):
        table = _derive("Employment", self.BODY).tables[0]
        self.assertFalse(table.column_for("vatNumber").mandatory)
        self.assertFalse(table.column_for("payrollRef").mandatory)

    def test_membership_check_allows_non_members_and_full_members(self):
        table = _derive("Employment", self.BODY).tables[0]
        check = next(c for c in table.checks
                     if c.name == "ck_party_employer_member")
        # Non-member: both guarded columns null. Member: the mandatory
        # qualifier present. A payroll reference without a VAT number fails.
        self.assertIn("vat_number IS NULL AND payroll_ref IS NULL",
                      check.expression)
        self.assertIn("vat_number IS NOT NULL", check.expression)
        self.assertNotIn("vat_number IS NOT NULL AND payroll_ref IS NOT NULL",
                         check.expression)

    def test_absorb_requires_a_mandatory_qualifier(self):
        with self.assertRaises(ValueError):
            _derive("Employment", """
object-type Party identified-by Party
object-type Employer identified-by Employer
fact payrollRef : Employer -> PayrollRef -- optional
Employer is a Party -- mapping: absorb
""")

    def test_absorb_rejects_a_default_on_a_subtype_fact(self):
        with self.assertRaises(ValueError):
            _derive("Employment", """
object-type Party identified-by Party
object-type Employer identified-by Employer
fact vatNumber : Employer -> VatNumber -- mandatory, default X
Employer is a Party -- mapping: absorb
""")

    def test_absorb_rejects_a_multivalued_subtype_fact(self):
        with self.assertRaises(ValueError):
            _derive("Employment", """
object-type Party identified-by Party
object-type Employer identified-by Employer
fact vatNumber : Employer -> VatNumber -- mandatory
fact contacts : Employer -> { Contact } -- zero or more
Employer is a Party -- mapping: absorb
""")

    def test_transitive_absorb_includes_ancestor_mandatory_facts(self):
        table = _derive("Staff", """
object-type Person identified-by Person
object-type Employee identified-by Employee
object-type Manager identified-by Manager
fact employeeNo : Employee -> Int -- mandatory
fact level : Manager -> Int -- mandatory
Employee is a Person -- mapping: absorb
Manager is a Employee -- mapping: absorb
""").tables[0]
        check = next(c for c in table.checks
                     if c.name == "ck_person_manager_member")
        self.assertIn("employee_no IS NOT NULL", check.expression)
        self.assertIn("level IS NOT NULL", check.expression)


class EntityReferenceConformanceTests(unittest.TestCase):

    def test_state_owning_target_gets_an_fk(self):
        model = _derive("Directory", """
object-type Department identified-by DeptCode
object-type Employee identified-by Employee
fact deptName : Department -> Name -- mandatory
fact worksFor : Employee -> Department -- mandatory
""")
        employee = next(t for t in model.tables
                        if t.table == "directory__employee")
        self.assertIn(
            "works_for -> directory__department(dept_code)",
            employee.foreign_keys)

    def test_reference_scheme_subject_resolves_to_the_entity_table(self):
        model = _derive("Legal", """
object-type Client identified-by ClientId
object-type Firm identified-by FirmUri
fact firmName : Firm -> Name -- mandatory
fact firmByClientId : ClientId -> FirmUri -- mandatory
""")
        client = next(t for t in model.tables
                      if t.table == "legal__client_id")
        self.assertIn("firm_by_client_id -> legal__firm(firm_uri)",
                      client.foreign_keys)

    def test_value_type_target_has_no_fk(self):
        model = _derive("Profiling", """
object-type UserId identified-by UserId
fact email : UserId -> Email -- mandatory
""")
        self.assertFalse(any(t.foreign_keys for t in model.tables))

    def test_identity_only_target_is_opaque_with_a_warning(self):
        model = _derive("Lending", """
object-type Member identified-by Member
object-type Loan identified-by Loan
fact borrower : Loan -> Member -- mandatory
""")
        self.assertFalse(any(t.foreign_keys for t in model.tables))
        self.assertTrue(any("owns no table" in warning
                            for warning in model.warnings), model.warnings)

    def test_reference_to_a_partitioned_supertype_is_rejected(self):
        with self.assertRaises(ValueError):
            _derive("Party", """
object-type Party identified-by Party
object-type Individual identified-by Individual
object-type Assignment identified-by Assignment
fact name : Party -> Name -- mandatory
fact assignee : Assignment -> Party -- mandatory
Individual is a Party -- mapping: partition
""")

    def test_foreign_key_cycle_is_rejected(self):
        with self.assertRaises(ValueError):
            _derive("Mutual", """
object-type A identified-by A
object-type B identified-by B
fact aName : A -> Name -- mandatory
fact bName : B -> Name -- mandatory
fact aToB : A -> B -- mandatory
fact bToA : B -> A -- mandatory
""")

    def test_cross_concept_fk_is_rejected(self):
        table = rmap.RelationSchema(
            "X", "x", "X",
            [rmap.Column("id", "id")], ["id"],
            ["id -> other(id)"], [], False)
        with self.assertRaises(ValueError):
            rmap._order_tables([table])

    def test_tables_are_ordered_before_their_fk_targets(self):
        model = _derive("Directory", """
object-type Department identified-by DeptCode
object-type Employee identified-by Employee
fact deptName : Department -> Name -- mandatory
fact worksFor : Employee -> Department -- mandatory
""")
        names = [table.table for table in model.tables]
        self.assertLess(names.index("directory__department"),
                        names.index("directory__employee"))

    def test_review_shows_the_identity_only_warning(self):
        text = """## Conceptual model

```
object-type Member identified-by Member
object-type Loan identified-by Loan
fact borrower : Loan -> Member -- mandatory
```
"""
        review = rmap.render_review("Lending", text)
        self.assertIn("## Warnings", review)
        self.assertIn("owns no table", review)

    def test_alter_adds_a_new_entity_foreign_key(self):
        baseline = rmap.model_descriptor([_derive("Directory", """
object-type Department identified-by DeptCode
object-type Employee identified-by Employee
fact deptName : Department -> Name -- mandatory
fact worksFor : Employee -> String -- mandatory
""")])
        current = rmap.model_descriptor([_derive("Directory", """
object-type Department identified-by DeptCode
object-type Employee identified-by Employee
fact deptName : Department -> Name -- mandatory
fact worksFor : Employee -> Department -- mandatory
""")])
        sql, warnings = rmap._alter_sql(baseline, current, "directory")
        self.assertIn('ADD CONSTRAINT "fk_directory__employee_works_for"',
                      sql)
        self.assertIn('FOREIGN KEY ("works_for") REFERENCES '
                      '"directory__department" ("dept_code")', sql)
        self.assertEqual(warnings, [])


class DataModelSemanticsConformanceTests(unittest.TestCase):

    def test_absorb_without_a_qualifier_fails_at_stage_03b(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type Party identified-by Party
object-type Employer identified-by Employer
fact payrollRef : Employer -> PayrollRef -- optional
Employer is a Party -- mapping: absorb
"""))
        self.assertTrue(any("no mandatory simple fact" in failure
                            for failure in failures), failures)

    def test_absorb_with_a_default_fails_at_stage_03b(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type Party identified-by Party
object-type Employer identified-by Employer
fact vatNumber : Employer -> VatNumber -- mandatory, default X
Employer is a Party -- mapping: absorb
"""))
        self.assertTrue(any("default" in failure for failure in failures),
                        failures)

    def test_absorb_with_a_multivalued_fact_fails_at_stage_03b(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type Party identified-by Party
object-type Employer identified-by Employer
fact vatNumber : Employer -> VatNumber -- mandatory
fact contacts : Employer -> { Contact } -- zero or more
Employer is a Party -- mapping: absorb
"""))
        self.assertTrue(any("multi-valued" in failure for failure in failures),
                        failures)

    def test_mixed_absorb_and_partition_fails_at_stage_03b(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type Party identified-by Party
object-type Employer identified-by Employer
object-type Individual identified-by Individual
fact vatNumber : Employer -> VatNumber -- mandatory
Employer is a Party -- mapping: absorb
Individual is a Party -- mapping: partition
"""))
        self.assertTrue(any("mixes absorb and partition" in failure
                            for failure in failures), failures)

    def test_ambiguous_reference_scheme_is_rejected(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type Person identified-by SharedId
object-type Vehicle identified-by SharedId
fact personName : Person -> Name -- mandatory
"""))
        self.assertTrue(any("identifies multiple object types" in failure
                            for failure in failures), failures)

    def test_subtype_sharing_the_root_scheme_is_not_ambiguous(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type Person identified-by PersonId
object-type Patient identified-by PersonId
fact personName : Person -> Name -- mandatory
Patient is a Person -- mapping: separate
"""))
        self.assertFalse(any("identifies multiple object types" in failure
                             for failure in failures), failures)

    def test_partitioned_supertype_reference_fails_at_stage_03b(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type Party identified-by Party
object-type Individual identified-by Individual
object-type Assignment identified-by Assignment
fact name : Party -> Name -- mandatory
fact assignee : Assignment -> Party -- mandatory
Individual is a Party -- mapping: partition
"""))
        self.assertTrue(any("partitioned supertype" in failure
                            for failure in failures), failures)


class RoleParticipationConformanceTests(unittest.TestCase):

    def test_value_mandatory_with_the_mandatory_subject_is_accepted(self):
        model = _derive("Org", """
object-type Employee identified-by Employee
object-type Department identified-by DeptCode
fact employeeName : Employee -> Name -- mandatory
fact deptName : Department -> Name -- mandatory
fact manages : Employee -> Department -- mandatory, unique, value mandatory
""")
        employee = next(t for t in model.tables
                        if t.table == "org__employee")
        self.assertTrue(employee.column_for("manages").mandatory)
        self.assertTrue(employee.column_for("manages").unique)
        self.assertEqual([], model.warnings)

    def test_1to1_oriented_on_the_optional_role_is_rejected(self):
        with self.assertRaises(ValueError):
            _derive("Org", """
object-type Employee identified-by Employee
object-type Department identified-by DeptCode
fact employeeName : Employee -> Name -- mandatory
fact deptName : Department -> Name -- mandatory
fact manages : Employee -> Department -- optional, unique, value mandatory
""")

    def test_value_role_on_a_value_type_is_rejected(self):
        with self.assertRaises(ValueError):
            _derive("Orders", """
object-type Order identified-by Order
fact status : Order -> Status -- value mandatory
""")

    def test_mandatory_value_role_on_a_non_1to1_fact_warns(self):
        model = _derive("Org", """
object-type Employee identified-by Employee
object-type Department identified-by DeptCode
fact employeeName : Employee -> Name -- mandatory
fact deptName : Department -> Name -- mandatory
fact worksFor : Employee -> Department -- mandatory, value mandatory
""")
        self.assertTrue(any("mandatory value role" in warning
                            for warning in model.warnings), model.warnings)


class MultiColumnUniqueConformanceTests(unittest.TestCase):

    def test_multi_column_unique_renders_a_table_constraint(self):
        model = _derive("TenantUsers", """
object-type User identified-by User
fact tenant : User -> Tenant -- mandatory
fact email : User -> Email -- mandatory
unique ( tenant, email )
""")
        table = model.tables[0]
        self.assertEqual(table.unique_groups,
                         [rmap.UniqueGroup(["tenant", "email"])])
        sql = rmap.render_migration("x", [model])
        self.assertIn('UNIQUE ("tenant", "email")', sql)

    def test_filtered_multi_column_unique_renders_a_partial_index(self):
        model = _derive("TenantUsers", """
object-type User identified-by User
fact tenant : User -> Tenant -- mandatory
fact email : User -> Email -- mandatory
fact deletedAt : User -> Timestamp -- optional
unique ( tenant, email ) while deletedAt absent
""")
        sql = rmap.render_migration("x", [model])
        self.assertIn(
            'CREATE UNIQUE INDEX IF NOT EXISTS '
            '"tenant_users_tenant_email_open_idx"', sql)
        self.assertIn('WHERE "deleted_at" IS NULL', sql)

    def test_cross_table_unique_is_rejected(self):
        with self.assertRaises(ValueError):
            _derive("Cross", """
object-type A identified-by A
object-type B identified-by B
fact aName : A -> Name -- mandatory
fact bName : B -> Name -- mandatory
unique ( aName, bName )
""")

    def test_multi_column_unique_predicate_must_be_simple(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type Order identified-by Order
fact tags : Order -> { Tag } -- zero or more
fact orderNumber : Order -> Number -- mandatory
unique ( tags, orderNumber )
"""))
        self.assertTrue(any("simple single-valued" in failure
                            for failure in failures), failures)

    def test_generated_model_carries_the_unique_constraint(self):
        spec = ap.ConceptSpec(
            name="TenantUsers", purpose="experiment",
            state_lines=[
                "tenant: User -> Tenant -- mandatory",
                "email: User -> Email -- mandatory",
                "unique ( tenant, email )",
            ],
            actions=[])
        text = gdm.render(spec)
        machine = ap.parse_machine_model(text)
        self.assertEqual(
            machine.unique_constraints,
            [ap.UniqueConstraint(("tenant", "email"))])
        self.assertEqual(vdm.check_machine_semantics(machine), [])


class SubtypeCompletenessConformanceTests(unittest.TestCase):

    DISCRIMINATED = """
object-type Party identified-by Party
object-type Employer identified-by Employer
fact partyName : Party -> Name -- mandatory
fact partyKind : Party -> PartyKind -- mandatory, in {individual, employer}
fact vatNumber : Employer -> VatNumber -- mandatory
Employer is a Party -- mapping: absorb, discriminator partyKind = employer
"""

    def test_discriminator_generates_an_explicit_membership_check(self):
        model = _derive("Employment", self.DISCRIMINATED)
        table = model.tables[0]
        check = next(c for c in table.checks
                     if c.name == "ck_party_employer_member")
        self.assertIn("party_kind = 'employer'", check.expression)
        self.assertIn("vat_number IS NOT NULL", check.expression)
        self.assertIn("vat_number IS NULL", check.expression)

    def test_discriminator_allows_an_optional_only_subtype(self):
        model = _derive("Employment", """
object-type Party identified-by Party
object-type Employer identified-by Employer
fact partyName : Party -> Name -- mandatory
fact partyKind : Party -> PartyKind -- mandatory
fact payrollRef : Employer -> PayrollRef -- optional
Employer is a Party -- mapping: absorb, discriminator partyKind = employer
""")
        check = next(c for c in model.tables[0].checks
                     if c.name == "ck_party_employer_member")
        self.assertIn("payroll_ref IS NULL", check.expression)
        self.assertIn("party_kind = 'employer'", check.expression)

    def test_disjoint_absorb_subtypes_get_a_pairwise_check(self):
        model = _derive("Employment", """
object-type Party identified-by Party
object-type Employer identified-by Employer
object-type Contractor identified-by Contractor
fact partyName : Party -> Name -- mandatory
fact vatNumber : Employer -> VatNumber -- mandatory
fact contractRef : Contractor -> Ref -- mandatory
Employer is a Party -- mapping: absorb
Contractor is a Party -- mapping: absorb
disjoint ( Employer, Contractor )
""")
        checks = " | ".join(c.expression for c in model.tables[0].checks)
        self.assertIn("vat_number IS NOT NULL", checks)
        self.assertIn("contract_ref IS NOT NULL", checks)
        self.assertIn("NOT (", checks)

    def test_disjoint_separate_subtypes_warn_not_enforced(self):
        model = _derive("Party", """
object-type Party identified-by Party
object-type Client identified-by Client
object-type Supplier identified-by Supplier
fact partyName : Party -> Name -- mandatory
fact discount : Client -> Int -- optional
fact credit : Supplier -> Int -- optional
Client is a Party -- mapping: separate
Supplier is a Party -- mapping: separate
disjoint ( Client, Supplier )
""")
        self.assertTrue(any("not enforced" in warning
                            for warning in model.warnings), model.warnings)

    def test_exhaustive_partition_is_inert(self):
        model = _derive("Party", """
object-type Party identified-by Party
object-type Client identified-by Client
object-type Supplier identified-by Supplier
fact partyName : Party -> Name -- mandatory
Client is a Party -- mapping: partition
Supplier is a Party -- mapping: partition
exhaustive ( Party )
""")
        self.assertFalse(any("exhaustive" in warning
                             for warning in model.warnings), model.warnings)

    def test_discriminator_requires_absorb(self):
        with self.assertRaises(ValueError):
            _derive("Party", """
object-type Party identified-by Party
object-type Client identified-by Client
fact partyName : Party -> Name -- mandatory
fact partyKind : Party -> PartyKind -- mandatory
fact discount : Client -> Int -- optional
Client is a Party -- mapping: separate, discriminator partyKind = client
""")

    def test_generated_model_carries_role_and_subtype_constraints(self):
        spec = ap.ConceptSpec(
            name="Employment", purpose="experiment",
            state_lines=[
                "partyName: Party -> Name -- mandatory",
                "partyKind: Party -> PartyKind -- mandatory, in {individual, employer}",
                "vatNumber: Employer -> VatNumber -- mandatory",
                "contractRef: Contractor -> Ref -- mandatory",
                "Employer is a Party -- mapping: absorb, discriminator partyKind = employer",
                "Contractor is a Party -- mapping: absorb",
                "disjoint ( Employer, Contractor )",
                "exhaustive ( Party )",
            ],
            actions=[])
        machine = ap.parse_machine_model(gdm.render(spec))
        self.assertEqual(machine.discriminators,
                         [("Employer", "partyKind", "employer")])
        self.assertEqual(machine.disjoint, [("Employer", "Contractor")])
        self.assertEqual(machine.exhaustive, ["Party"])
        self.assertEqual(vdm.check_machine_semantics(machine), [])

    def test_generated_value_role_carries_through(self):
        spec = ap.ConceptSpec(
            name="Org", purpose="experiment",
            state_lines=[
                "employeeName: Employee -> Name -- mandatory",
                "deptName: Department -> Name -- mandatory",
                "manages: Employee -> Department -- mandatory, unique, value mandatory",
            ],
            actions=[])
        machine = ap.parse_machine_model(gdm.render(spec))
        manages = next(f for f in machine.facts if f.field == "manages")
        self.assertEqual(ap.role_flags(manages.multiplicity), (True, True))
        self.assertEqual(vdm.check_machine_semantics(machine), [])

    def test_stage03b_rejects_disjoint_across_supertypes(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type A identified-by A
object-type B identified-by B
object-type C identified-by C
fact aName : A -> Name -- mandatory
fact bName : B -> Name -- mandatory
fact cName : C -> Name -- mandatory
B is a A -- mapping: absorb
C is a A -- mapping: absorb
disjoint ( B, C )
"""))
        # Same supertype is valid; the check below uses a genuinely bad case.
        self.assertEqual(failures, [])
        bad = vdm.check_machine_semantics(_machine("""
object-type A identified-by A
object-type D identified-by D
object-type B identified-by B
object-type C identified-by C
fact aName : A -> Name -- mandatory
fact dName : D -> Name -- mandatory
fact bName : B -> Name -- mandatory
fact cName : C -> Name -- mandatory
B is a A -- mapping: absorb
C is a D -- mapping: absorb
disjoint ( B, C )
"""))
        self.assertTrue(any("share one" in failure for failure in bad), bad)


class RichTypeConformanceTests(unittest.TestCase):

    RICH = """
object-type Entity identified-by Entity
fact amount : Entity -> Decimal(12,2) -- mandatory
fact externalId : Entity -> UUID -- mandatory
fact bornOn : Entity -> Date -- optional
fact opensAt : Entity -> Time -- optional
fact metadata : Entity -> JSONB -- optional
fact payload : Entity -> Bytes -- optional
"""

    def test_built_in_scalar_types_render(self):
        model = _derive("RichTypes", self.RICH)
        columns = {c.predicate: c.sql_type for c in model.tables[0].columns}
        self.assertEqual(columns["amount"], "NUMERIC(12,2)")
        self.assertEqual(columns["externalId"], "UUID")
        self.assertEqual(columns["bornOn"], "DATE")
        self.assertEqual(columns["opensAt"], "TIME")
        self.assertEqual(columns["metadata"], "JSONB")
        self.assertEqual(columns["payload"], "BYTEA")
        sql = rmap.render_migration("x", [model])
        self.assertIn('"amount" numeric(12,2) NOT NULL', sql)
        self.assertIn('"external_id" uuid NOT NULL', sql)
        self.assertIn('"metadata" jsonb', sql)
        self.assertIn('"payload" bytea', sql)

    def test_type_map_overrides_a_domain_type(self):
        model = _derive("Money", """
object-type Wallet identified-by Wallet
fact balance : Wallet -> Money -- mandatory
""", type_map={"Money": "NUMERIC(12,2)"})
        self.assertEqual(model.tables[0].column_for("balance").sql_type,
                         "NUMERIC(12,2)")
        self.assertIn('"balance" numeric(12,2) NOT NULL',
                      rmap.render_migration("x", [model]))

    def test_unregistered_domain_type_defaults_to_text(self):
        model = _derive("Mail", """
object-type User identified-by User
fact email : User -> Email -- mandatory
""")
        self.assertEqual(model.tables[0].column_for("email").sql_type, "TEXT")

    def test_strict_types_reject_an_unregistered_domain_type(self):
        with self.assertRaises(ValueError):
            _derive("Mail", """
object-type User identified-by User
fact email : User -> Email -- mandatory
""", strict_types=True)

    def test_type_config_reads_properties_and_feature_override(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "features" / "UC-01-x"
            (feature / "_config").mkdir(parents=True)
            (root / "clad.properties").write_text(
                "storage.type.Money=NUMERIC(12,2)\n"
                "storage.type.strict=true\n", encoding="utf-8")
            (feature / "_config" / "type-map.md").write_text(
                "Email=CITEXT\n", encoding="utf-8")
            mapping, strict = rmap._type_config_for(str(root), str(feature))
            self.assertEqual(mapping, {"Money": "NUMERIC(12,2)",
                                       "Email": "CITEXT"})
            self.assertTrue(strict)


class UnsupportedConstructTests(unittest.TestCase):

    def test_derived_fact_is_rejected_by_derivation(self):
        with self.assertRaises(ValueError):
            _derive("DerivedProbe", """
object-type Order identified-by Order
fact total : Order -> Int -- derived
""")

    def test_derived_fact_fails_at_stage_03b(self):
        failures = vdm.check_machine_semantics(_machine("""
object-type Order identified-by Order
fact total : Order -> Int -- derived
"""))
        self.assertTrue(any("derived" in failure for failure in failures),
                        failures)

    def test_set_comparison_clause_is_reported_not_dropped(self):
        machine = _machine("""
object-type Employee identified-by Employee
fact employeeName : Employee -> Name -- mandatory
constraint subset employeeName
""")
        self.assertTrue(any("unrecognized" in error
                            for error in machine.errors), machine.errors)


if __name__ == "__main__":
    unittest.main()
