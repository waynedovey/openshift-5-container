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

    def test_end_to_end(self):
        guide = GUIDE.read_text()
        self.assertIn("/ws/data/load", guide)
        self.assertIn("/ws/data/all", guide)
        self.assertIn("/ws/backends/list", guide)


if __name__ == "__main__":
    unittest.main()
