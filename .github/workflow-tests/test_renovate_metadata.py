"""Keep every CodeQL component discoverable by the shared Renovate updater."""

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "workflow_contracts", ROOT / "scripts/workflow_contracts.py"
)
contracts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contracts)


class RenovateMetadataTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(ROOT / ".github/workflows", self.root / ".github/workflows")
        shutil.copyfile(ROOT / ".release-policy.json", self.root / ".release-policy.json")

    def change_sarif_comment(self, comment):
        path = self.root / ".github/workflows/scorecards.yml"
        lines = path.read_text().splitlines(keepends=True)
        changed = 0
        for index, line in enumerate(lines):
            if "uses: github/codeql-action/upload-sarif@" in line:
                lines[index] = line.split(" #", 1)[0].rstrip() + comment + "\n"
                changed += 1
        self.assertEqual(changed, 1)
        path.write_text("".join(lines))

    def test_current_workflows_satisfy_required_contract(self):
        contracts.validate(self.root)

    def test_sarif_without_release_comment_is_rejected(self):
        self.change_sarif_comment("")
        with self.assertRaisesRegex(ValueError, "inline full release comment"):
            contracts.validate(self.root)

    def test_sarif_with_a_different_release_comment_is_rejected(self):
        self.change_sarif_comment(" # v0.0.1")
        with self.assertRaisesRegex(ValueError, "same release"):
            contracts.validate(self.root)
