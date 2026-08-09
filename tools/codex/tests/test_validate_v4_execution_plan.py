from __future__ import annotations

import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = PROJECT_ROOT / "tools" / "codex" / "validate_v4_execution_plan.py"
PLAN_PATH = PROJECT_ROOT / "docs" / "global_modernization" / "v4" / "EXECUTION_UNIT_INDEX.json"
SOURCE_PATH = PROJECT_ROOT / "docs" / "global_modernization" / "v3" / "WORK_PACKAGE_INDEX.yaml"

spec = importlib.util.spec_from_file_location("validate_v4_execution_plan", VALIDATOR_PATH)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class V4ExecutionPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.source = validator.load_source_ledger(SOURCE_PATH)

    def codes(self, plan: dict) -> set[str]:
        return {finding["code"] for finding in validator.validate(plan, self.source)["findings"]}

    def test_current_plan_passes(self) -> None:
        self.assertEqual(validator.validate(self.plan, self.source)["status"], "PASS")

    def test_duplicate_unit_fails(self) -> None:
        plan = deepcopy(self.plan)
        plan["units"].append(deepcopy(plan["units"][0]))
        self.assertIn("DUPLICATE_UNIT_ID", self.codes(plan))

    def test_unknown_dependency_fails(self) -> None:
        plan = deepcopy(self.plan)
        plan["units"][1]["depends_on"] = ["MISSING-UNIT"]
        self.assertIn("UNKNOWN_DEPENDENCY", self.codes(plan))

    def test_missing_source_coverage_fails(self) -> None:
        plan = deepcopy(self.plan)
        next(unit for unit in plan["units"] if unit["id"] == "M02-DEC")["source_packages"] = []
        self.assertIn("MISSING_MANDATORY_SOURCE_COVERAGE", self.codes(plan))

    def test_conditional_mandatory_mix_fails(self) -> None:
        plan = deepcopy(self.plan)
        next(unit for unit in plan["units"] if unit["id"] == "M02-AAB")["source_packages"] = ["M02.8"]
        self.assertIn("CONDITIONAL_UNIT_HAS_MANDATORY_SOURCE", self.codes(plan))

    def test_dependency_cycle_fails(self) -> None:
        plan = deepcopy(self.plan)
        next(unit for unit in plan["units"] if unit["id"] == "RDX-01")["depends_on"] = ["TC-01"]
        self.assertIn("DEPENDENCY_CYCLE", self.codes(plan))

    def test_execution_ledger_drift_fails(self) -> None:
        plan = deepcopy(self.plan)
        plan["execution_ledger"]["mandatory_remaining"] -= 1
        self.assertIn("EXECUTION_LEDGER_COUNT_MISMATCH", self.codes(plan))

    def test_schema_shape_fails(self) -> None:
        plan = deepcopy(self.plan)
        del plan["units"][0]["objective"]
        self.assertIn("PLAN_SCHEMA_VIOLATION", self.codes(plan))

    def test_duplicate_decision_fails(self) -> None:
        plan = deepcopy(self.plan)
        plan["decisions"].append(deepcopy(plan["decisions"][0]))
        self.assertIn("DUPLICATE_DECISION_ID", self.codes(plan))


if __name__ == "__main__":
    unittest.main()
