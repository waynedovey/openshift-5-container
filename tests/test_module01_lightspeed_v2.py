"""Module 1: test Lightspeed diagnosis of an incorrect MongoDB Service targetPort."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "content/modules/ROOT/pages/module-01-whats-new-in-ocp5.adoc"
MANIFEST = ROOT / "content/modules/ROOT/examples/module01-mongodb.yaml"


class LightspeedWorkshopTests(unittest.TestCase):
    def test_read_only_prompt(self):
        guide = GUIDE.read_text()
        self.assertIn("OpenShift Lightspeed 2.0", guide)
        self.assertIn("Troubleshooting", guide)
        self.assertIn("Do not read Secrets or change anything.", guide)
        self.assertIn("namespace {user}-demo", guide)
        self.assertIn("inspect Pods, Services and logs", guide)

    def test_fault_is_mongodb_target_port(self):
        guide = GUIDE.read_text()
        manifest = MANIFEST.read_text()
        self.assertIn("== Mission 5: Repair the MongoDB Service", guide)
        self.assertIn("targetPort: 27017", guide)
        self.assertIn("targetPort: 27018", manifest)
        self.assertIn("port: 27017", manifest)
        self.assertIn("quay.io/mongodb/mongodb-community-server:8.0.32-ubi9-slim", manifest)
        self.assertNotIn("intentionally-broken-backend", guide)
        self.assertNotIn("intentionally-broken-backend", manifest)
        self.assertNotIn("registry.redhat.io/rhmap47/mongodb", guide)

    def test_live_lightspeed_screenshots_and_cli_fix(self):
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
        self.assertIn("| 0–1 | 1–6 | 6–11 | 11–17 | 17–21 | 21–24 | 24–27 | 27–28 min", guide)
        self.assertIn("| 25–30 min (rehearsal target)", index)
        self.assertNotIn("50-minute console-first", index)

    def test_end_to_end(self):
        guide = GUIDE.read_text()
        self.assertIn("/ws/data/load", guide)
        self.assertIn("/ws/data/all", guide)
        self.assertIn("/ws/backends/list", guide)


if __name__ == "__main__":
    unittest.main()
