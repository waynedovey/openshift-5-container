# Module 2 preflight — Gitea, Argo CD, Lightspeed MCP

This workshop intentionally uses **one GitOps-owned ConfigMap**, not the
National Parks Deployments/Services/Secrets deployed in Module 1.

## Before provisioning students

1. Merge the Module 2 change upstream before provisioning the lab. The
   `automation/gitops/bootstrap-tenant/values.yaml` migration source is
   `https://github.com/rhpds/openshift-5-container`. It must contain
   `content/modules/ROOT/examples/module02-gitops/` on its default branch.
2. Re-run tenant Gitea provisioning. For each student in
   `user-<guid>-demo`, confirm there is a readable and **editable** Gitea
   repository named `openshift-5-container`, containing both
   `kustomization.yaml` and `national-parks-gitops-info.yaml`.
   The Gitea operator's generated username is the student username;
   `gitea.password` controls the Gitea password separately from OpenShift.
3. Confirm student Gitea repositories are *not read-only mirrors*. The
   generated student account must be able to commit through Gitea's
   Edit File screen. Check repository ownership before class.
4. Check the student's OpenShift namespace already contains the `argocd`
   ArgoCD custom resource, Argo CD server route and working SSO. The
   bootstrap currently creates **no Argo CD Application**; students create
   `national-parks-settings` manually.
5. In the Argo CD instance, confirm the `default` AppProject accepts
   **ConfigMaps only for this exercise**; the Application must target the
   student's own `user-<guid>-demo` namespace. The student must have
   permission through SSO to create and manually sync an Application.
6. Confirm the Argo CD repo-server can reach the **Gitea HTTPS clone URL**
   without credentials for the public student repository. Validate DNS and
   certificate trust, rather than disabling TLS verification.
7. Ensure the student can log into the Showroom Terminal as `user-<guid>`.
   `oc whoami` must never remain the Showroom ServiceAccount. Confirm
   `oc get applications.argoproj.io` and ConfigMaps are readable.
8. Confirm Lightspeed 2.0's built-in MCP read tools can inspect native
   resources in the student namespace. Reading the Argo CD CRD via MCP may
   be unavailable; the student guide provides `oc get` and UI fallbacks.
9. Keep **auto-sync, prune, self-heal and force disabled**. Never point the
   student's Application at the repository root or the Module 1 manifest
   path. Only the single ConfigMap in `module02-gitops` may be applied.
10. Check that the National Parks map and `/ws/data/all` still work after
    completing the GitOps exercise.

## OpenShift 5 feature checks (read-only)

- Confirm `oc version` reports an OpenShift 5.0 cluster. The workshop
  targets OpenShift 5 but does not assume that every optional component is installed.
- In Lightspeed 2.0 *Troubleshooting*, students must inspect **actual MCP
  read-tool calls** and compare their namespace and results with `oc get`
  output. No MCP write approval is required. If the toolset cannot read
  `applications.argoproj.io`, use the OpenShift CLI and Argo CD UI.
- **OpenShift GitOps 1.22 console plug-in (GA):** verify whether the optional
  plug-in is installed and enabled. If present, students may view
  `national-parks-settings` in the OpenShift console. If absent, use the
  standalone Argo CD tab. Do not install a plug-in during the lab.
- **OpenShift 5 console:** Glass, High Contrast and Traditional UI themes
  can be explored if the appearance selector is available. This is optional.
- **Source Hydrator and environment promotions:** GitOps 1.22 offers these
  as Technology Preview features. Students learn about the concept, but do
  not enable either feature. This workshop still uses standard Kustomize.
- **Tenant controls:** verify student RBAC before using Lightspeed. The
  demonstration is read-only and does not create NetworkPolicies or
  UserDefinedNetworks in the shared cluster.
- GitOps, Kustomize, RBAC, manual sync and Operator Lifecycle Manager
  `ClusterExtension` are not newly introduced by OpenShift 5. Do not
  present these established APIs as new 5.0 features.

References:
- https://www.redhat.com/en/blog/announcing-red-hat-openshift-5
- https://developers.redhat.com/articles/2026/11/09/red-hat-openshift-5-for-developers

## Screenshot capture and student interaction

The updated Module 2 student guide has **12 renderable SVG screenshot placeholders**
and three prediction/answer checkpoints. Screenshot inventory and final PNG
filenames are in `content/modules/ROOT/images/MODULE02-SCREENSHOTS.md`.
Students must **not** upload or edit images.

- Instructor captures real evidence from a disposable student environment,
  redacting passwords, tokens, Secret values and unrelated namespaces.
- Capture S02/S10 with actual read-only Lightspeed MCP tool calls visible.
- Capture S05/S09 before sync and S06/S11 after sync; screenshots must match
  the exact ConfigMap and `national-parks-settings` Application.
- S07 is optional and requires an enabled OpenShift GitOps console plug-in.
  Leave the placeholder if the optional plug-in is not installed.
- Replace an SVG reference with a PNG reference **only after** committing
  the real PNG, then check the rendered Showroom page.
- The collapsible checkpoint answers are teaching aids. Test that they
  render and reveal on the actual Antora/Showroom deployment.

## Student demonstration

- Initial Argo CD Application (before first Sync): OutOfSync/Missing.
- After first manual Sync: `national-parks-gitops-info.data.message`
  equals `GitOps baseline`.
- Student edits the ConfigMap **in their Gitea repo** to
  `Updated in Gitea` and commits the tracked branch.
- After Refresh and before Sync: Application is OutOfSync, and the live
  ConfigMap still says `GitOps baseline`.
- The student asks Lightspeed to investigate using **read-only** MCP tools.
  It should identify manual synchronization from the Application state.
  This is a goal, **not a guaranteed model result**; don't accept hallucinated
  Git contents or approval to change resources.
- After reviewed manual Sync: `oc get configmap` reports
  `Updated in Gitea`; `nationalparks` workloads were not changed.
- Student RBAC tests show access to their project and restricted access
  to `openshift-config` (verify your cluster's actual permissions first).

## Dependencies and next module

Module 3 and Module 5 were drafted before this redesign and assume
Argo CD already owns the complete application. **They must be revised
before delivery**, because Module 2 intentionally does not adopt those
workloads. Do not automatically synchronize Deployment changes from their
old exercises.

Run two fresh student accounts end to end before marking Module 2 ready.
No live Gitea/Argo CD rehearsal has been performed by this PR.
