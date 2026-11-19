"""Module 1: test scoped, approved MCP repair of an incorrect MongoDB targetPort."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "content/modules/ROOT/pages/module-01-whats-new-in-ocp5.adoc"
MANIFEST = ROOT / "content/modules/ROOT/examples/module01-mongodb.yaml"


class LightspeedWorkshopTests(unittest.TestCase):
    def test_read_only_diagnosis_before_write(self):
        guide = GUIDE.read_text()
        self.assertIn("OpenShift Lightspeed 2.0", guide)
        self.assertIn("Troubleshooting", guide)
        self.assertIn("Do not inspect Secrets, execute shell", guide)
        self.assertIn("namespace {user}-demo", guide)
        self.assertIn("use resources_get to inspect only these two resources", guide)
        self.assertIn("Do not list other Pods or Services.", guide)
        self.assertIn("Service/mongodb-nationalparks", guide)
        self.assertIn("Deployment/mongodb-nationalparks", guide)
        self.assertIn("user-clcvz-demo", guide)

    def test_fault_is_mongodb_target_port(self):
        guide = GUIDE.read_text()
        manifest = MANIFEST.read_text()
        self.assertIn("== Mission 5: Approve and verify Lightspeed's MongoDB Service repair", guide)
        self.assertIn("targetPort: 27017", guide)
        self.assertIn("targetPort: 27018", manifest)
        self.assertIn("port: 27017", manifest)
        self.assertIn("quay.io/mongodb/mongodb-community-server:8.0.32-ubi9-slim", manifest)
        self.assertNotIn("intentionally-broken-backend", guide)
        self.assertNotIn("intentionally-broken-backend", manifest)
        self.assertNotIn("registry.redhat.io/rhmap47/mongodb", guide)

    def test_live_lightspeed_screenshots_and_cli_fallback(self):
        guide = GUIDE.read_text()
        images = ROOT / "content/modules/ROOT/images"
        names = [
            "module01-s07-lightspeed-root-cause.png",
            "module01-s07a-lightspeed-fix-console.png",
            "module01-s07b-lightspeed-fix-oc.png",
        ]
        for name in names:
            self.assertTrue((images / name).exists(), name)
            self.assertIn(f"image::{name}[", guide)
        self.assertIn("oc patch svc mongodb-nationalparks -n {user}-demo", guide)
        self.assertIn('"path":"/spec/ports/0/targetPort","value":27017', guide)
        self.assertIn("Live Lightspeed 2 diagnosis", guide)

    def test_mcp_write_is_primary_and_human_approval_explicit(self):
        guide = GUIDE.read_text()
        index = (ROOT / "content/modules/ROOT/pages/index.adoc").read_text()
        preflight = (ROOT / "docs/instructor/module-01-deployment-preflight.md").read_text()
        self.assertIn("resources_create_or_update", guide)
        self.assertIn("actual MCP tool-approval workflow", guide)
        self.assertIn("not the named value", guide)
        self.assertIn("numeric value 27017", guide)
        self.assertIn("Keep all existing Service metadata", guide)
        self.assertIn("Do not modify Secrets, Deployments", guide)
        self.assertIn("approval interface", guide)
        self.assertIn("Manual recovery fallback (only if the approved MCP path fails)", guide)
        self.assertIn("oc auth can-i patch services", guide)
        self.assertIn("oc auth can-i update services", guide)
        self.assertIn("manual fallback", index)
        self.assertIn("19 November 2026", preflight)
        self.assertIn("The copied conversation did not include a visible", preflight)
        self.assertNotIn("MCP write tools are not required.", guide)

    def test_load_only_after_port_repair(self):
        guide = GUIDE.read_text()
        self.assertLess(guide.index("== Mission 5:"), guide.index("/ws/data/load[Load National Parks data"))
        self.assertLess(guide.index("/ws/data/load[Load National Parks data"), guide.index("== Mission 6:"))
        self.assertIn("27017 -> 27017", guide)
        self.assertIn("*Checkpoint 3:*", guide)

    def test_dynamic_urls_and_showroom(self):
        guide = GUIDE.read_text()
        host = "{user}-demo.{openshift_cluster_ingress_domain}"
        self.assertIn(f"https://national-parks-app-{host}/ws/data/load[", guide)
        self.assertIn(f"https://national-parks-app-{host}/ws/data/all[", guide)
        self.assertIn(f"https://parksmap-{host}/ws/backends/list[", guide)
        self.assertIn(f"https://parksmap-{host}/[", guide)
        self.assertIn("window=_blank", guide)
        self.assertIn("Showroom's right-hand pane", guide)
        config = (ROOT / "ui-config.yml").read_text()
        self.assertIn("name: ParksMap", config)
        self.assertIn("name: National Parks API", config)
        self.assertIn("https://national-parks-app-${USER}-demo.${DOMAIN}", config)

    def test_module_one_timing_is_28_minutes(self):
        import re
        guide = GUIDE.read_text()
        index = (ROOT / "content/modules/ROOT/pages/index.adoc").read_text()
        headings = re.findall(
            r"^== Mission [0-6]:[^\n]*\((\d+) minutes?\)$",
            guide, re.MULTILINE
        )
        signoff = re.search(
            r"^== Mission complete:[^\n]*\((\d+) minutes?\)$",
            guide, re.MULTILINE
        )
        self.assertEqual([int(x) for x in headings], [1, 5, 5, 6, 4, 3, 3])
        self.assertIsNotNone(signoff)
        self.assertEqual(sum(map(int, headings)) + int(signoff.group(1)), 28)
        self.assertIn("25–30-minute", guide)
        self.assertIn("| Time | Mission", guide)
        timeline = [int(x) for x in re.findall(r"^\| (\d+) min \| ", guide, re.MULTILINE)]
        self.assertEqual(timeline, [1, 5, 5, 6, 4, 3, 3, 1])
        self.assertIn("| 25–30 min (rehearsal target)", index)
        self.assertNotIn("50-minute console-first", index)

    def test_end_to_end(self):
        guide = GUIDE.read_text()
        self.assertIn("/ws/data/load", guide)
        self.assertIn("/ws/data/all", guide)
        self.assertIn("/ws/backends/list", guide)


if __name__ == "__main__":
    unittest.main()
