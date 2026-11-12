# Module 1 instructor preflight: Service selector troubleshooting

Students deploy ParksMap, Python National Parks and **working MongoDB 8**.
After loading park records, they deliberately change the Python backend
**Service** selector (`spec.selector.app`) to `intentionally-broken-backend`.
Lightspeed 2.0 reads live Pods, Services and Routes to diagnose the missing
endpoints. Students restore the selector in the console. **No MCP write tools
or MongoDB image updates are required.**

## Before class

1. **Terminal authentication is required.** The Showroom terminal initially uses
   `system:serviceaccount:user-<guid>-showroom:showroom`, which may have no
   permission to patch Deployments in `user-<guid>-demo`. Students must
   use the OpenShift console's *Copy login command*, log in as
   `user-<guid>`, verify `oc whoami` and `oc auth can-i patch
   deployments.apps -n user-<guid>-demo` returns `yes`.
   Do not expand the Showroom ServiceAccount's permissions.
2. Check that Argo CD and Gitea already exist in the project. **Do not
   delete them**, and make sure Argo CD is not automatically reconciling
   the student-created National Parks resources.
3. Check permissions to create Secrets, ConfigMaps, Deployments, Services,
   Routes and the ParksMap discovery Role/RoleBinding, plus permission to
   **edit the backend Service** and read Kubernetes resources with Lightspeed.
4. Verify the ParksMap image can pull, the `nationalparks-py` Dockerfile
   builds, and the MongoDB 8 image
   `quay.io/mongodb/mongodb-community-server:8.0.32-ubi9-slim` starts.
   MongoDB uses disposable `emptyDir` storage and a per-student Secret.
5. **Mandatory before students open the map:** verify that the `parksmap-discovery`
   ServiceAccount, Role and RoleBinding exist in each student project. The RoleBinding
   alone is insufficient. Check that the `parksmap` Deployment and current Pod
   use `serviceAccountName: parksmap-discovery`. Never grant `view` to `default`.
   Also verify the backend Service and Route have `type=parksmap-backend`.
6. Load disposable data by visiting the backend `/ws/data/load` **once**.
   Confirm `/ws/data/all` contains records **before breaking connectivity**.
7. Record the **actual backend Service name** (`national-parks-app` in the
   current lab, or the name actually generated), its `spec.selector`, and matching Pod labels.
   Test the one-value change below using a fresh student. Do not modify the
   MongoDB Service or Deployment.

## Mandatory student prechecks

After the RBAC manifest is applied, the student patches the Deployment
as their own account (never the Showroom ServiceAccount):

```bash
oc patch deployment parksmap -n user-<guid>-demo --type=merge \
  -p '{"spec":{"template":{"spec":{"serviceAccountName":"parksmap-discovery"}}}}'
oc rollout status deployment/parksmap -n user-<guid>-demo
```

Require output `deployment.apps/parksmap patched` before trusting the
rollout status. A successful rollout can refer to an unchanged Deployment.

After Mission 1, the student verifies:

```bash
oc get deployment parksmap -n user-<guid>-demo \
  -o jsonpath='{.spec.template.spec.serviceAccountName}{"\n"}'
```

Expected: `parksmap-discovery`. A blank result means the default ServiceAccount
is still in use; correct the Deployment before moving on.

After deliberately breaking the backend Service selector in Mission 3,
confirm the Service has no **ready endpoints** and that its Pods remain Running.
Never proceed to the Lightspeed prompt while the Service still matches Pods.

## Rehearse the fault and repair

In the backend Service YAML, replace **only** the existing
`spec.selector.app` value:

```yaml
spec:
  selector:
    app: intentionally-broken-backend
```

Keep other selector entries unchanged. The backend Service should have no
matching endpoints, while the Python Pod remains Running and its Route
stops serving the backend.

Run the short read-only Lightspeed prompt in Mission 4. Require live evidence
of the mismatched Service selector and backend Pod labels. The student then
restores `spec.selector.app` to the value recorded from the matching Pods.
Verify:

- Backend Route `https://national-parks-app-<user>-demo.<ingress-domain>/ws/data/all` returns nonempty park data.
- ParksMap `https://parksmap-<user>-demo.<ingress-domain>/ws/backends/list` finds the Python backend.
- The map displays park markers.

The Service fault is repeatable without deleting Pods, Secrets or data.
**Do not reset the whole student namespace.**

## Limitations

- This is a static manifest contract, not a completed live-cluster smoke test.
  Rehearse with two fresh student accounts.
- The built-in Lightspeed 2.0 MCP deployment may provide read tools only;
  students use the OpenShift console for the Service update.
- Keep Argo CD auto-sync disabled before Module 2 onboarding; otherwise
  GitOps could immediately reverse the deliberate fault.
- Existing tenant quotas include Argo CD and Gitea. Do not introduce an
  additional restrictive quota in Module 1.

## Files

- [Student guide](../../content/modules/ROOT/pages/module-01-whats-new-in-ocp5.adoc)
- [MongoDB 8 manifest](../../content/modules/ROOT/examples/module01-mongodb.yaml)
- [ParksMap discovery RBAC](../../content/modules/ROOT/examples/module01-parksmap-discovery.yaml)
