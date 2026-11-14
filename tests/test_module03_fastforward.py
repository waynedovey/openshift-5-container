"""Regression guards for the student-only Module 3 fast-forward helper."""

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation/scripts/prepare-module03-baseline.sh"
GUIDE = ROOT / "docs/instructor/module03-fast-forward-bootstrap.md"


class Module03BaselineBootstrapTests(unittest.TestCase):
    def test_bash_syntax_and_help(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)
        result = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True, text=True, check=True,
        )
        self.assertIn("--sync-gitea", result.stdout)
        self.assertIn("--resume-demo", result.stdout)
        self.assertIn("--only-demo", result.stdout)
        self.assertIn("--only-gitops", result.stdout)
        self.assertIn("user-<guid>", result.stdout)

    def test_source_and_namespace_ownership(self):
        script = SCRIPT.read_text()
        self.assertIn('STUDENT="$(oc whoami', script)
        self.assertIn('DEMO_NS="${STUDENT}-demo"', script)
        self.assertIn('GITOPS_NS="${STUDENT}-gitops"', script)
        self.assertIn('APPLICATION=national-parks-settings', script)
        self.assertIn('source.repoURL', script)
        self.assertIn('prune: false', script)
        self.assertIn('selfHeal: true', script)
        self.assertIn('RespectIgnoreDifferences=true', script)
        self.assertNotIn('oc create namespace', script)
        self.assertNotIn('oc delete namespace', script)
        self.assertNotIn('git push --force', script)
        self.assertNotIn('oc patch approvalpolicy', script)

    def test_module1_dependency_order_and_safe_data_seed(self):
        script = SCRIPT.read_text()
        order = [
            'oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/00-mongodb-credentials.yaml"',
            'oc wait -n "$DEMO_NS" --for=condition=complete job/nationalparks-credentials-bootstrap',
            'oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/01-mongodb.yaml"',
            'wait_rollout "$DEMO_NS" mongodb-nationalparks',
            'oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/02-nationalparks-backend.yaml"',
            'wait_rollout "$DEMO_NS" nationalparks',
            'oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/03-parksmap-discovery.yaml"',
            'oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/04-parksmap-frontend.yaml"',
            'wait_rollout "$DEMO_NS" parksmap',
        ]
        indices = [script.index(text) for text in order]
        self.assertEqual(indices, sorted(indices))
        self.assertIn('if [[ "$count" == 0 ]]', script)
        self.assertIn('if [[ "$count" == 3 ]]', script)
        self.assertIn('if [[ "$broken_port" == \'27018\' ]]', script)
        self.assertIn('if [[ "$count" != 0 && "$RESUME_DEMO" != true ]]', script)
        self.assertIn('if [[ "$count" == 0 ]]', script)
        self.assertIn('if [[ "$count" == 0 ]]; then', script)
        self.assertIn('"https://$api_host/ws/data/load"', script)

    def test_no_cmp_requirement_in_minimal_lab_terminal(self):
        script = SCRIPT.read_text()
        self.assertNotIn("python3 cmp mktemp", script)
        self.assertNotIn("cmp -s", script)
        self.assertIn("git diff --no-index --quiet --", script)
        self.assertIn("for tool in oc git curl python3 mktemp awk", script)

    def test_student_gitea_requires_opt_in_to_update(self):
        script = SCRIPT.read_text()
        self.assertIn('if [[ "$SYNC_GITEA" != true ]]', script)
        self.assertIn('if [[ "$ONLY_DEMO" != true ]]; then preflight_gitops; fi', script)
        self.assertIn('if [[ "$ONLY_GITOPS" != true ]]; then prepare_demo; fi', script)
        self.assertIn('git diff --cached --check', script)
        self.assertIn('git push origin main', script)
        self.assertIn('GITEA_TOKEN', script)
        self.assertIn('fullstack/kustomization.yaml', script)
        self.assertIn('fullstack/national-parks-gitops-info.yaml', script)
        self.assertIn('fullstack/04-parksmap-frontend.yaml', script)
        self.assertIn("Preserve the student's harmless Module 2 checkpoint message", script)
        self.assertIn('Existing $APPLICATION points to unexpected Gitea/destination', script)

    def test_health_verification_covers_more_than_pod_readiness(self):
        script = SCRIPT.read_text()
        self.assertIn('get_deploy_ready', script)
        self.assertIn('/ws/data/all', script)
        self.assertIn('/ws/backends/list', script)
        self.assertIn('http_code', script)
        self.assertIn('status" == Synced', script)
        self.assertIn('health" == Healthy', script)
        self.assertIn('print_diagnostics', script)
        self.assertIn('does not terminate', script)
        self.assertIn('PARTIAL BASELINE', script)
        self.assertIn('Run again without --only-*', script)

    def test_instructor_guide_mentions_limits(self):
        guide = GUIDE.read_text()
        for required in (
            'Copy login command', '--sync-gitea', 'partially',
            'original', 'readiness', 'ClusterResourceQuota',
            'Secret', 'Argo CD', 'not', 'Module 3',
        ):
            self.assertIn(required.lower(), guide.lower())


if __name__ == "__main__":
    unittest.main()
