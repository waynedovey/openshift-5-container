"""Contracts for Module 3 Agentic Application Operations on the National Parks stack."""

import re
import subprocess
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "content/modules/ROOT/pages/module-03-agentic-application-operations.adoc"
INDEX = ROOT / "content/modules/ROOT/pages/index.adoc"
NAV = ROOT / "content/modules/ROOT/nav.adoc"
MODULE2 = ROOT / "content/modules/ROOT/pages/module-02-gitops-onboarding-multitenancy.adoc"
MODULE4 = ROOT / "content/modules/ROOT/pages/module-04-ai-assisted-incident-investigation.adoc"
SOURCE = ROOT / "content/modules/ROOT/examples/module02-gitops/fullstack"
SCRIPT = ROOT / "automation/scripts/create-module03-agentic-run.sh"
INSTRUCTOR = ROOT / "docs/instructor/module-03-agentic-app-deployment-preflight.md"


class AgenticApplicationOperationsTests(unittest.TestCase):
    def test_five_mission_40_minute_practical_module(self):
        guide = MODULE.read_text()
        missions = re.findall(r"^== Mission [1-5]:", guide, re.MULTILINE)
        self.assertEqual(len(missions), 5, missions)
        self.assertIn("*Estimated time: 40 minutes*", guide)
        self.assertEqual(guide.count("[%collapsible]"), 3)
        for topic in (
            "GitOps", "AgenticRun", "Lightspeed", "Troubleshooting",
            "MCP", "Gitea", "Synced", "Healthy", "Proposed", "readinessProbe",
            "ClusterResourceQuota", "OOMKilled", "port: 18080",
            "port: http", "Module 4",
        ):
            with self.subTest(topic=topic):
                self.assertIn(topic, guide)
        self.assertIn("== Troubleshooting", guide)
        self.assertIn("== Completion check", guide)
        self.assertIn("== References", guide)

    def test_student_isolation_and_gitops_source_of_truth(self):
        guide = MODULE.read_text()
        self.assertIn('LAB_NAMESPACE="$STUDENT-demo"', guide)
        self.assertIn('GITOPS_NAMESPACE="$STUDENT-gitops"', guide)
        self.assertIn('ARGOCD_NAMESPACE="$STUDENT-demo"', guide)
        self.assertIn("national-parks-settings", guide)
        self.assertIn(
            "content/modules/ROOT/examples/module02-gitops/fullstack/04-parksmap-frontend.yaml",
            guide,
        )
        self.assertIn("student Gitea", guide)
        self.assertIn("do *not* change", guide.lower())
        self.assertNotIn("oc patch approvalpolicy", guide)
        self.assertNotIn("oc apply -f -", guide)
        self.assertNotIn("oc delete ", guide)
        self.assertNotIn("oc scale ", guide)
        self.assertNotIn("oc patch deployment", guide)
        self.assertNotIn("oc create namespace", guide)
        self.assertIn("Do *not* click manual Sync", guide)
        self.assertIn("Restore", guide)

    def test_actual_manifest_has_healthy_named_readiness_port(self):
        frontend = list(yaml.safe_load_all(
            (SOURCE / "04-parksmap-frontend.yaml").read_text()
        ))
        backend = list(yaml.safe_load_all(
            (SOURCE / "02-nationalparks-backend.yaml").read_text()
        ))
        parksmap = next(d for d in frontend if d["kind"] == "Deployment")
        nationalparks = next(d for d in backend if d["kind"] == "Deployment")
        container = parksmap["spec"]["template"]["spec"]["containers"][0]
        self.assertEqual(container["ports"][0]["containerPort"], 8080)
        self.assertEqual(container["readinessProbe"]["tcpSocket"]["port"], "http")
        self.assertEqual(
            parksmap["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"],
            "2",
        )
        self.assertEqual(
            nationalparks["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"],
            "1",
        )
        self.assertEqual(container["name"], "parksmap")
        self.assertEqual(container["resources"]["limits"]["memory"], "768Mi")

        guide = MODULE.read_text()
        self.assertIn("port: 18080", guide)
        self.assertIn("port: http", guide)
        self.assertIn("fix(module03): restore ParksMap readiness port", guide)
        # The checked-in canonical GitOps source is healthy; students inject
        # and revert the temporary fault only in their own Gitea copies.

    def test_instructor_script_creates_only_an_analysis_run(self):
        script = SCRIPT.read_text()
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)
        help_text = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            check=True, capture_output=True, text=True,
        ).stdout
        self.assertIn("analysis-only AgenticRun", help_text)
        self.assertIn("does NOT", help_text)

        self.assertIn('target_namespace="$student-gitops"', script)
        self.assertIn('run_name="parksmap-$student-readiness"', script)
        self.assertIn("oc get crd agenticruns.agentic.openshift.io", script)
        self.assertIn('oc get agent default -n "$operator_namespace"', script)
        self.assertIn("oc auth can-i create", script)
        self.assertIn('if [[ "$live_probe_port" != "18080" ]]', script)
        self.assertIn("oc create -f -", script)
        self.assertNotIn("oc patch approvalpolicy", script)
        self.assertNotIn("oc delete ", script)
        self.assertNotIn("oc scale ", script)
        self.assertNotIn("oc get secret", script)

        token = "cat <<YAML | oc create -f -\n"
        self.assertEqual(script.count(token), 1)
        cr = script.split(token, 1)[1].split("\nYAML\n", 1)[0]
        resource = yaml.safe_load(cr)
        self.assertEqual(resource["apiVersion"], "agentic.openshift.io/v1alpha1")
        self.assertEqual(resource["kind"], "AgenticRun")
        self.assertEqual(resource["metadata"]["namespace"], "$operator_namespace")
        self.assertEqual(resource["spec"]["analysis"], {"agent": "default"})
        self.assertIn("Investigate", resource["spec"]["request"])
        self.assertNotIn("execution", resource["spec"])
        self.assertNotIn("verification", resource["spec"])

    def test_student_quota_check_uses_applied_quota(self):
        guide = MODULE.read_text()
        self.assertIn("appliedclusterresourcequotas.quota.openshift.io", guide)
        self.assertIn("oc describe appliedclusterresourcequota", guide)
        self.assertIn("Shared quota details are restricted", guide)
        self.assertNotIn("oc describe clusterresourcequota", guide)

    def test_agentic_fallback_and_instructor_gate(self):
        guide = MODULE.read_text()
        instructor = INSTRUCTOR.read_text()
        self.assertIn("AgenticRun: not available / not authorized", guide)
        self.assertIn("If Agentic Runs are unavailable", guide)
        self.assertIn("Do not click Execute Remediation", guide)
        self.assertIn("one", instructor.lower())
        self.assertIn("one instructor demonstration at a time", instructor)
        self.assertIn("agenticruns.agentic.openshift.io", instructor)
        self.assertIn("llmprovider", instructor)
        self.assertIn("analysis-only", instructor)
        self.assertIn("Module 4", instructor)
        self.assertIn("Do not inject", instructor)

    def test_nav_and_module_continuity(self):
        nav = NAV.read_text()
        index = INDEX.read_text()
        module2 = MODULE2.read_text()
        module4 = MODULE4.read_text()
        slug = "module-03-agentic-application-operations.adoc"
        self.assertTrue(MODULE.is_file())
        self.assertIn(slug, nav)
        self.assertIn(slug, index)
        self.assertIn(slug, module2)
        self.assertNotIn("module-03-workload-management-resource-controls.adoc", nav)
        self.assertNotIn("module-03-workload-management-resource-controls.adoc", index)
        self.assertNotIn("module-03-workload-management-resource-controls.adoc", module2)
        self.assertIn("Agentic Application Operations", nav)
        self.assertIn("Agentic Application Operations", index)
        self.assertIn("40 min", index)
        self.assertIn("backend", module4.lower())
        self.assertIn("xref:module-04-ai-assisted-incident-investigation.adoc", MODULE.read_text())


if __name__ == "__main__":
    unittest.main()
