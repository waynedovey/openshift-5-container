"""Protect Module 3 bootstrap source and student Gitea repository contracts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "content/modules/ROOT/pages/module-03-agentic-application-operations.adoc"
SCRIPT = ROOT / "automation/scripts/prepare-module03-baseline.sh"


class Module03GiteaBaselineTests(unittest.TestCase):
    def test_student_downloads_maintained_helper(self):
        module = MODULE.read_text()
        self.assertIn(
            "https://raw.githubusercontent.com/rhpds/openshift-5-container/main/"
            "automation/scripts/prepare-module03-baseline.sh", module
        )
        self.assertNotIn(
            "openshift-5-container-workspace/main/scripts/prepare-module03-baseline.sh",
            module,
        )

    def test_student_gitea_matches_bootstrap_repository(self):
        script = SCRIPT.read_text()
        self.assertIn(
            "https://github.com/rhpds/openshift-5-container-workspace.git", script
        )
        self.assertIn(
            '$GITEA_BASE/$STUDENT/openshift-5-container-workspace.git', script
        )
        self.assertIn(
            '$GITEA_BASE/api/v1/repos/$STUDENT/openshift-5-container-workspace',
            script,
        )
        self.assertIn('GIT_TERMINAL_PROMPT=0 git', script)
        self.assertIn('reconcile-gitea-repositories.sh -n $DEMO_NS', script)


if __name__ == "__main__":
    unittest.main()
