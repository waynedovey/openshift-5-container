"""Module 2 GitOps source, student lab and tenant provisioning contracts."""

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "content/modules/ROOT/pages/module-02-gitops-onboarding-multitenancy.adoc"
SOURCE = ROOT / "content/modules/ROOT/examples/module02-gitops"
BOOTSTRAP = ROOT / "automation/gitops/bootstrap-tenant/values.yaml"
UI_CONFIG = ROOT / "ui-config.yml"
INSTRUCTOR = ROOT / "docs/instructor/module-02-gitops-preflight.md"


class GitOpsWorkshopTests(unittest.TestCase):
    def test_module02_screenshot_placeholders(self):
        import re

        guide = GUIDE.read_text()
        checklist = (ROOT / "content/modules/ROOT/images/MODULE02-SCREENSHOTS.md").read_text()
        images_dir = ROOT / "content/modules/ROOT/images"
        refs = re.findall(r"image::(module02-s\d{2}[-\w]*\.(?:svg|png))\[", guide)
        self.assertEqual(len(refs), 12, refs)
        self.assertEqual(len(set(refs)), 12)
        for name in refs:
            path = images_dir / name
            self.assertTrue(path.is_file(), name)
            self.assertIn(name.replace(".svg", ".png"), checklist)
            if name.endswith(".svg"):
                self.assertIn("SCREENSHOT NEEDED", path.read_text())
        self.assertEqual(len(re.findall(r"^\| S\d{2} \|", checklist, re.MULTILINE)), 12)
        self.assertIn("Students are never instructed to upload", checklist)

    def test_module02_has_interactive_student_checkpoints(self):
        guide = GUIDE.read_text()
        self.assertEqual(guide.count("[%collapsible]"), 3)
        self.assertIn("*Predict before syncing:*", guide)
        self.assertIn("*Predict:* Where does the new message exist now", guide)
        self.assertIn("*Think:* Would NetworkPolicy", guide)
        self.assertEqual(len(__import__("re").findall(r"^== Mission [1-5]:", guide, __import__("re").MULTILINE)), 5)

    def test_only_one_safe_gitops_resource(self):
        kustomization = yaml.safe_load((SOURCE / "kustomization.yaml").read_text())
        self.assertEqual(kustomization["kind"], "Kustomization")
        self.assertEqual(kustomization["resources"], ["national-parks-gitops-info.yaml"])

        resource = yaml.safe_load((SOURCE / "national-parks-gitops-info.yaml").read_text())
        self.assertEqual(resource["kind"], "ConfigMap")
        self.assertEqual(resource["metadata"]["name"], "national-parks-gitops-info")
        self.assertNotIn("namespace", resource["metadata"])
        self.assertEqual(resource["data"]["message"], "GitOps baseline")
        self.assertNotIn("Secret", (SOURCE / "national-parks-gitops-info.yaml").read_text())

    def test_tenant_bootstrap_imports_source_repo(self):
        values = yaml.safe_load(BOOTSTRAP.read_text())
        migrated = {x["name"]: x for x in values["gitea"]["migrateRepos"]}
        self.assertIn("openshift-starter-guides", migrated)
        self.assertIn("openshift-5-container", migrated)
        self.assertEqual(migrated["openshift-5-container"]["url"],
                         "https://github.com/rhpds/openshift-5-container")
        self.assertFalse(migrated["openshift-5-container"]["private"])

    def test_student_authentication_and_manual_sync(self):
        guide = GUIDE.read_text()
        self.assertIn("oc login {openshift_api_url} -u {user} -p {password}", guide)
        self.assertIn("oc whoami", guide)
        self.assertIn("oc project {user}-demo", guide)
        self.assertNotIn("sed 's|system:serviceaccount", guide)
        self.assertIn("Sync policy | **Manual**", guide)
        self.assertIn("Do not read Secrets or change anything.", guide)
        self.assertIn("module02-gitops", guide)
        self.assertIn("national-parks-settings", guide)
        self.assertIn("OutOfSync", guide)
        self.assertIn("Updated in Gitea", guide)

    def test_gitops_cannot_accidentally_adopt_module_one_workloads(self):
        guide = GUIDE.read_text()
        self.assertIn("one harmless ConfigMap", guide)
        self.assertIn("one ConfigMap", guide)
        self.assertIn("do not sync", guide.lower())
        self.assertIn("not its Deployments, Secrets, Services or MongoDB settings", guide)
        self.assertNotIn("oc scale deployment/nationalparks", guide)
        self.assertIn("Argo CD currently manages **only the GitOps learning ConfigMap**", guide)

    def test_student_namespace_and_ui(self):
        guide = GUIDE.read_text()
        ui = UI_CONFIG.read_text()
        self.assertIn("oc auth can-i patch deployments.apps -n openshift-config", guide)
        self.assertIn("oc get rolebinding parksmap-discovery", guide)
        self.assertIn("https://parksmap-{user}-demo.{openshift_cluster_ingress_domain}/", guide)
        self.assertIn("name: Gitea", ui)
        self.assertIn("https://gitea-${USER}-demo.${DOMAIN}", ui)
        self.assertIn("name: ArgoCD", ui)

    def test_openshift_5_features_have_active_student_checkpoints(self):
        guide = GUIDE.read_text()
        self.assertIn("== What's new in OpenShift 5?", guide)
        self.assertIn("oc version", guide)
        self.assertIn("MCP server for Red Hat OpenShift", guide)
        self.assertIn("Expand the MCP tool calls", guide)
        self.assertIn("OpenShift GitOps 1.22 console plug-in", guide)
        self.assertIn("OpenShift 5 console integration (optional", guide)
        self.assertIn("Source Hydrator and environment promotions", guide)
        self.assertIn("Technology Preview", guide)
        self.assertIn("NetworkPolicy restricts Pod traffic", guide)
        self.assertIn("UserDefinedNetwork", guide)
        self.assertIn("Do not enable", guide)
        self.assertIn("If no GitOps entry appears", guide)
        self.assertIn("An Argo CD Application has a target namespace", guide)

    def test_openshift_5_does_not_change_safety_boundaries(self):
        guide = GUIDE.read_text()
        self.assertEqual(guide.count("Do not read Secrets or change anything."), 2)
        self.assertIn("Sync policy | **Manual**", guide)
        self.assertIn("one harmless ConfigMap", guide)
        self.assertIn("does not create or change network policies", guide)
        self.assertNotIn("oc patch svc mongodb-nationalparks", guide)
        self.assertNotIn("oc apply -f clusterextension", guide)

    def test_instructor_preflight_has_release_gate(self):
        instructions = INSTRUCTOR.read_text()
        self.assertIn("Merge the Module 2 change upstream", instructions)
        self.assertIn("not read-only mirrors", instructions)
        self.assertIn("No live Gitea/Argo CD rehearsal", instructions)


if __name__ == "__main__":
    unittest.main()
