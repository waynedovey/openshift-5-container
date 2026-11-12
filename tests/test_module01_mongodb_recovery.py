"""Validate the working MongoDB 8 manifest used in Module 1."""
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "content/modules/ROOT/examples/module01-mongodb.yaml"
SECRET = "nationalparks-mongodb-parameters"

class MongoDBManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resources = list(yaml.safe_load_all(MANIFEST.read_text()))
        cls.by_kind = {x["kind"]: x for x in cls.resources}
        cls.deployment = cls.by_kind["Deployment"]
        cls.container = cls.deployment["spec"]["template"]["spec"]["containers"][0]

    def test_working_image_and_three_resources(self):
        self.assertEqual(set(self.by_kind), {"ConfigMap", "Deployment", "Service"})
        self.assertEqual(self.container["image"], "quay.io/mongodb/mongodb-community-server:8.0.32-ubi9-slim")
        self.assertNotIn("namespace", self.deployment["metadata"])
        self.assertNotIn("registry.redhat.io/rhmap47/mongodb", MANIFEST.read_text())

    def test_secret_and_init_script(self):
        self.assertEqual(self.container["envFrom"], [{"secretRef": {"name": SECRET}}])
        env = {item["name"]: item for item in self.container["env"]}
        self.assertEqual(env["MONGO_INITDB_ROOT_PASSWORD"]["valueFrom"]["secretKeyRef"]["key"], "MONGODB_ADMIN_PASSWORD")
        self.assertEqual(env["MONGO_INITDB_DATABASE"]["valueFrom"]["secretKeyRef"]["key"], "MONGODB_DATABASE")
        mounts = {item["name"]: item for item in self.container["volumeMounts"]}
        self.assertEqual(mounts["modern-data"]["mountPath"], "/data/db")
        self.assertEqual(mounts["app-user-bootstrap"]["mountPath"], "/docker-entrypoint-initdb.d")
        self.assertIn("createUser(", self.by_kind["ConfigMap"]["data"]["create-app-user.js"])

    def test_internal_database_service_matches_pod_labels(self):
        service = self.by_kind["Service"]
        self.assertEqual(service["spec"]["type"], "ClusterIP")
        pod_labels = self.deployment["spec"]["template"]["metadata"]["labels"]
        for key, value in service["spec"]["selector"].items():
            self.assertEqual(pod_labels[key], value)

if __name__ == "__main__":
    unittest.main()
