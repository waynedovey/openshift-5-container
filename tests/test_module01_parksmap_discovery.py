"""Validate the isolated, read-only ParksMap backend discovery resources."""

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "content/modules/ROOT/examples/module01-parksmap-discovery.yaml"
GUIDE = ROOT / "content/modules/ROOT/pages/module-01-whats-new-in-ocp5.adoc"


class ParksMapDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resources = list(yaml.safe_load_all(MANIFEST.read_text()))
        cls.by_kind = {obj["kind"]: obj for obj in cls.resources}

    def test_only_expected_namespace_scoped_resources(self):
        self.assertEqual(set(self.by_kind), {"ServiceAccount", "Role", "RoleBinding"})
        for resource in self.resources:
            self.assertEqual(resource["metadata"]["name"], "parksmap-discovery")
            self.assertNotIn("namespace", resource["metadata"])

    def test_discovery_is_read_only_and_excludes_secrets(self):
        role_rules = self.by_kind["Role"]["rules"]
        by_resource = {resource: rule for rule in role_rules
                       for resource in rule["resources"]}
        self.assertEqual(set(by_resource), {"routes", "services", "endpoints"})
        for resource in ("routes", "services"):
            self.assertEqual(set(by_resource[resource]["verbs"]),
                             {"get", "list", "watch"})
        self.assertEqual(set(by_resource["endpoints"]["verbs"]),
                         {"get", "watch"})
        self.assertEqual(set(by_resource["endpoints"]["resourceNames"]),
                         {"nationalparks", "national-parks-app"})

    def test_binding_and_documentation_use_dedicated_identity(self):
        binding = self.by_kind["RoleBinding"]
        self.assertEqual(binding["roleRef"]["name"], "parksmap-discovery")
        self.assertEqual(binding["subjects"], [{
            "kind": "ServiceAccount", "name": "parksmap-discovery",
            "namespace": "{user}-demo",
        }])
        guide = GUIDE.read_text()
        self.assertIn('[source,yaml,subs="attributes+"]\n----\n'
                      'include::example$module01-parksmap-discovery.yaml[]', guide)
        self.assertNotIn("STUDENT_NAMESPACE_REPLACE_ME", guide)
        self.assertIn("serviceAccountName: parksmap-discovery", guide)
        self.assertIn("oc patch deployment parksmap -n {user}-demo --type=merge", guide)
        self.assertIn("oc rollout status deployment/parksmap -n {user}-demo", guide)
        self.assertIn("oc whoami", guide)
        self.assertIn("oc login {openshift_api_url} -u {user} -p {password}", guide)
        screenshot = ROOT / "content/modules/ROOT/images/module01-student-login-success.svg"
        self.assertTrue(screenshot.exists())
        self.assertIn("image::module01-student-login-success.svg[", guide)
        self.assertIn("[REDACTED]", screenshot.read_text())
        self.assertNotIn("alSnFt4fTGWo", screenshot.read_text())
        self.assertNotIn("-p alSnFt4fTGWo", guide)
        self.assertLess(guide.index("oc login {openshift_api_url}"), guide.index("oc patch deployment parksmap"))
        self.assertIn("oc auth can-i patch deployments.apps", guide)
        self.assertIn("deployment.apps/parksmap patched", guide)
        self.assertIn("A successful rollout **alone** does not mean a failed patch succeeded.", guide)
        self.assertIn("Required: enable ParksMap backend discovery", guide)
        self.assertIn("oc get deployment parksmap -n {user}-demo", guide)
        self.assertIn("Do not continue until this check passes.", guide)
        self.assertIn("Do not give `view` to the `default` ServiceAccount.", guide)
        self.assertLess(guide.index("=== Required: enable ParksMap backend discovery"),
                        guide.index("Your browser may ask whether the site can"))
        self.assertIn("/ws/backends/list", guide)
        self.assertIn("A RoleBinding alone does not make the Pod use this identity", guide)

    def test_rendered_student_namespace_matches_project(self):
        rendered = MANIFEST.read_text().replace("{user}", "user-fc45j")
        resources = list(yaml.safe_load_all(rendered))
        binding = next(obj for obj in resources if obj["kind"] == "RoleBinding")
        self.assertEqual(binding["subjects"][0]["namespace"], "user-fc45j-demo")


if __name__ == "__main__":
    unittest.main()
