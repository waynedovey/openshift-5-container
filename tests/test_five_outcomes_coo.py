"""Curriculum contracts for the five outcomes and instructor-scoped COO/Perses."""
import re
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "content/modules/ROOT/pages"
MODULE2 = PAGES / "module-02-gitops-onboarding-multitenancy.adoc"
MODULE3 = PAGES / "module-03-agentic-application-operations.adoc"
MODULE4 = PAGES / "module-04-ai-assisted-incident-investigation.adoc"
MODULE5 = PAGES / "module-05-gitops-remediation-app-lifecycle.adoc"
COO = ROOT / "automation/observability/monitoring-uiplugin.yaml"
PREFLIGHT = ROOT / "docs/instructor/cluster-observability-workshop-preflight.md"


class FiveOutcomeTests(unittest.TestCase):
    def test_network_canary_scope_and_cleanup(self):
        text = MODULE2.read_text()
        heredocs = re.findall(
            r"cat <<'YAML' \| oc apply -n \"\$GITOPS_NAMESPACE\" -f -\n(.*?)\nYAML",
            text, re.S,
        )
        self.assertEqual(len(heredocs), 2)
        objs = [o for heredoc in heredocs for o in yaml.safe_load_all(heredoc)]
        self.assertEqual({o["kind"] for o in objs},
                         {"Deployment", "Service", "NetworkPolicy"})
        policy = next(o for o in objs if o["kind"] == "NetworkPolicy")
        self.assertEqual(policy["spec"]["podSelector"]["matchLabels"],
                         {"app": "workshop-netcheck"})
        self.assertEqual(policy["spec"]["policyTypes"], ["Ingress"])
        self.assertEqual(policy["spec"]["ingress"][0]["from"][0]["podSelector"], {})
        self.assertNotIn("namespaceSelector", policy["spec"]["ingress"][0]["from"][0])
        for obj in objs:
            self.assertNotIn("namespace", obj["metadata"])
        self.assertIn("oc delete networkpolicy workshop-netcheck-ingress", text)
        self.assertIn("oc delete deployment workshop-netcheck", text)
        self.assertIn("same-student cross-namespace", text)
        self.assertIn("cross-student", text)

    def test_weather_module_points_to_real_workspace(self):
        guide = MODULE4.read_text()
        self.assertIn("openshift-5-container-workspace → main", guide)
        self.assertNotIn("your student account → openshift-5-container → main", guide)
        self.assertIn("measure National Parks workload usage", guide)
        self.assertNotIn("Module 3 taught you to investigate the National Parks frontend and restore its readiness", guide)

    def test_workload_and_incident_not_repeated(self):
        m3, m4 = MODULE3.read_text(), MODULE4.read_text()
        self.assertNotIn("port: 18080", m3)
        self.assertIn("port: 18080", m4)
        self.assertIn("oc adm top pods", m3)
        self.assertIn("oc adm top pods", m4)
        self.assertIn("oc logs deployment/weathernow", m4)
        self.assertIn("oc get events", m4)
        self.assertIn("no change", m3.lower())
        self.assertIn("AgenticRuns remain *deferred*", m3)
        self.assertNotIn("cat <<YAML | oc create", m3)

    def test_coo_is_instructor_only_and_perses_enabled(self):
        obj = yaml.safe_load(COO.read_text())
        self.assertEqual(obj["kind"], "UIPlugin")
        self.assertEqual(obj["spec"]["type"], "Monitoring")
        self.assertTrue(obj["spec"]["monitoring"]["perses"]["enabled"])
        self.assertIn("instructor", COO.read_text().lower())
        guide = PREFLIGHT.read_text()
        self.assertIn("30 concurrent students", guide)
        self.assertIn("tenant", guide.lower())
        self.assertIn("not", guide.lower())
        self.assertIn("Perses", guide)

    def test_student_perses_dashboard_is_versioned_and_tenant_scoped(self):
        template = ROOT / "automation/observability/workshop-workloads-dashboard.yaml"
        dashboard = yaml.safe_load(template.read_text())
        self.assertEqual(dashboard["apiVersion"], "perses.dev/v1alpha2")
        self.assertEqual(dashboard["kind"], "PersesDashboard")
        self.assertEqual(dashboard["metadata"]["name"], "workshop-workloads")
        self.assertEqual(dashboard["metadata"]["namespace"], "__NAMESPACE__")
        panels = dashboard["spec"]["config"]["panels"]
        self.assertEqual(set(panels), {"cpuUsage", "memoryUsage", "restarts", "podReady"})
        for panel in panels.values():
            query = panel["spec"]["queries"][0]["spec"]["plugin"]["spec"]["query"]
            self.assertIn('namespace="__NAMESPACE__"', query)

        example = yaml.safe_load((
            ROOT / "automation/observability/workshop-workloads-datasource.EXAMPLE.yaml"
        ).read_text())
        self.assertEqual(example["kind"], "PersesDatasource")
        self.assertEqual(example["metadata"]["namespace"], "__NAMESPACE__")
        self.assertEqual(example["spec"]["config"]["plugin"]["kind"], "PrometheusDatasource")
        self.assertEqual(
            example["spec"]["config"]["plugin"]["spec"]["proxy"]["spec"]["url"],
            "__TENANT_METRICS_PROXY_URL__",
        )
        self.assertNotIn("PersesGlobalDatasource", template.read_text())
        script = (ROOT / "automation/observability/prepare-student-perses-dashboard.sh").read_text()
        self.assertIn("--tenant-query-isolation-verified", script)
        self.assertIn("status", script)
        self.assertIn("DRY RUN", script)
        self.assertNotIn("cluster-monitoring-view", script)

    def test_perses_student_screenshot_slots_are_real_placeholders(self):
        refs = {
            MODULE3: ("module03-s05-perses-workload-dashboard.svg",
                      "module03-s06-perses-metrics-comparison.svg"),
            MODULE4: ("module04-s16-perses-weather-readiness.svg",),
            MODULE5: ("module05-s13-perses-recovery-metrics.svg",),
        }
        for module_path, images in refs.items():
            content = module_path.read_text()
            for filename in images:
                with self.subTest(module=module_path.name, image=filename):
                    self.assertIn("image::" + filename, content)
                    asset = ROOT / "content/modules/ROOT/images" / filename
                    self.assertTrue(asset.is_file())
                    self.assertIn("SCREENSHOT NEEDED", asset.read_text())
        self.assertIn("workshop-workloads", MODULE3.read_text())
        self.assertIn("workshop-workloads", MODULE4.read_text())
        preflight = PREFLIGHT.read_text()
        self.assertIn("COO 1.5.5", preflight)
        self.assertIn("backend", preflight.lower())
        self.assertIn("prepare-student-perses-dashboard.sh", preflight)

    def test_release_recovery_requires_real_sha_and_route(self):
        guide = MODULE5.read_text()
        self.assertIn("full Git SHA", guide)
        self.assertIn(".status.sync.revision", guide)
        self.assertIn("oc rollout status", guide)
        self.assertIn("ImagePullBackOff", guide)
        self.assertIn("HTTP 200", guide)


if __name__ == "__main__":
    unittest.main()
