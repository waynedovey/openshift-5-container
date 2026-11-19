# Module 1 instructor preflight: MongoDB Service port

Students deploy the National Parks frontend, Python API and MongoDB 8.
**Intentional fault:** MongoDB listens on port `27017`, but its Service
forwards to `targetPort: 27018`. The MongoDB Pod can be Ready while the API
cannot connect. Students use OpenShift Lightspeed 2.0.1+ Troubleshooting to diagnose the
fault and perform an *approved* `resources_create_or_update` repair. A
one-field manual Service edit is the fallback, not the primary task.

## Target delivery time

**25–30 minutes** for the console-first student lab, with a **28-minute**
guided walkthrough: project 1, frontend/RBAC 5, Python backend build 5,
MongoDB fault 6, Lightspeed diagnosis 4, approved MCP repair 3,
application/map verification 3, and sign-off 1 minute.

Allow **2 minutes of transitions** within a 30-minute session. This is a
*rehearsal target*, not a measured guarantee: image pulls, build pipelines,
student authentication, RBAC, MCP write exposure and human approval must be validated
during preflight. Slow cluster startup or permissions troubleshooting are
out-of-band setup issues, not additional required student exercises.

## Before class

1. Authenticate the Showroom terminal as the assigned student, **not** the
   Showroom ServiceAccount. Verify `oc whoami` returns `user-<guid>`.
2. Verify `get`, `patch`, and `update` on Services in `user-<guid>-demo` as
   the student. MCP uses the calling identity; keep every student limited to
   their own namespace. Do not grant broad permissions to the Showroom
   ServiceAccount.
3. Ensure the `parksmap-discovery` ServiceAccount, Role and RoleBinding exist.
   The `parksmap` Deployment must use that ServiceAccount.
4. Confirm the frontend image pulls, Python backend builds, and
   `quay.io/mongodb/mongodb-community-server:8.0.32-ubi9-slim` starts.
5. Check the database Secret exists, with five correct keys, and the Python
   backend uses `envFrom.secretRef.name: nationalparks-mongodb-parameters`.
   Do not expose credentials.
6. Ensure Argo CD auto-sync will not overwrite student-created National Parks
   resources; leave pre-provisioned Argo CD and Gitea workloads alone.
7. Verify Lightspeed Operator `2.0.1` or newer and the running `openshift-mcp-server`
   Deployment. The operator-managed MCP ConfigMap must contain both
   `read_only = false` and `disable_destructive = false`, and tool discovery
   must offer `resources_get` and `resources_create_or_update`.
8. Verify the generated `olsconfig` contains `tools_approval.approval_type:
   tool_annotations` and that the actual approval interface works for an MCP
   write. An English sentence saying "I request approval" is not the approval UI.
   Keep tool-result inspection enabled. One RHOAI/vLLM Qwen3 test produced
   a `data_exfiltration` false positive reading an ordinary ConfigMap; if this
   happens again, use the manual fallback and record it. Do not disable
   guardrails or grant cluster-wide RBAC to students.

## Expected broken state

The manifest `content/modules/ROOT/examples/module01-mongodb.yaml` imports
a MongoDB Deployment and an internal Service. Verify:

```yaml
# MongoDB Deployment container
containerPort: 27017

# MongoDB Service
port: 27017
targetPort: 27018  # deliberately incorrect
```

Kubernetes can still mark the MongoDB Pod Ready, and the Service may still
have ready EndpointSlices. **Do not diagnose this as a selector mismatch.**
The Service forwards traffic to the wrong port.

The backend data endpoint at
`https://national-parks-app-<user>-demo.<ingress-domain>/ws/data/all`
should not return park records. Do not use `/ws/data/load` until the repair.

## Lightspeed and repair

1. As a fresh student, complete Mission 4's **read-only** investigation
   using **only** `resources_get` for `Service/mongodb-nationalparks` and
   `Deployment/mongodb-nationalparks` in `user-<guid>-demo`. Do not start
   with a broad query listing Pods, Services and logs: Qwen3 repeatedly
   misclassified one of those results as `data_exfiltration` in rehearsal.
   Check that Lightspeed identifies `targetPort: 27018` versus container
   port `27017`. A named target port `mongodb` is **valid**, so do not
   mistakenly call it a mismatch.
2. In Mission 5, the student sends the scoped write request, explicitly
   limiting the update to Service `mongodb-nationalparks` in their own
   `user-<guid>-demo` namespace and to numeric `spec.ports[0].targetPort: 27017`.
   The MCP `resources_create_or_update` tool requires the existing complete
   Service manifest and must preserve all other fields.
3. The student reviews the **actual tool approval request** and approves only
   if the proposed change is confined to that single Service field. If the
   model only states "I request approval" in prose, prompt it to invoke the
   tool rather than interpreting prose as a tool approval.
4. Have the student independently verify:

   ```bash
   oc get svc mongodb-nationalparks -n user-<guid>-demo \
     -o jsonpath='{.spec.ports[0].port}{" -> "}{.spec.ports[0].targetPort}{"\n"}'
   ```

   Expected after the repair: `27017 -> 27017`. A matching value proves
   the **Service changed**, but the approval UI must be observed separately
   before calling the full human-in-the-loop workflow verified.
5. If the write tool is missing, inspection rejects a benign tool response,
   the approval UI is unavailable, or the proposed manifest affects other
   fields, fall back to the OpenShift console YAML editor. A scoped CLI
   alternative is:

   ```bash
   oc patch svc mongodb-nationalparks -n user-<guid>-demo \
     --type=json \
     -p='[{"op":"replace","path":"/spec/ports/0/targetPort","value":27017}]'
   ```

   Record whether MCP or manual fallback made the change. Do **not**
   broaden RBAC, change Secrets, disable tool-result inspection, edit
   Deployments, or approve unrelated operations.

6. After the Service is healthy, load the disposable park dataset **once**
   using `/ws/data/load`; verify `/ws/data/all` returns records and
   ParksMap displays markers.

### Live rehearsal evidence

- **19 November 2026**, student `user-clcvz-demo`: broad "inspect Pods,
  Services and logs" queries repeatedly hit a Qwen3 safety classifier
  rejection (category `data_exfiltration`). A narrower two-resource
  `resources_get` prompt successfully reported `targetPort: 27018`
  versus container port `27017`. The filtered log excerpt did not identify
  which specific result was rejected; keep the safety guardrail enabled and
  use the focused read path in Mission 4.
- **12 November 2026**, student `user-6k7ww-demo`: the Lightspeed
  Troubleshooting read path identified the port mismatch and recommended
  restoring port `27017`.
- **19 November 2026**, student `user-dpfvh-demo`: Lightspeed identified
  `targetPort: 27018`, produced an update proposal and subsequently
  reported executing the Service repair. An independent student
  `oc get svc` returned `27017 -> 27017`. This confirms the effective
  resource change. **The copied conversation did not include a visible
  tool-approval UI capture**, so a separate preflight still needs to verify
  the human-in-the-loop control.

Before workshop delivery, rehearse with two fresh student accounts. Capture
actual before/after state, the real approval UI, and the updated screenshots
for Mission 5. Keep the current console-edit screenshot as the documented
manual fallback, not as evidence of automated approval.

**Do not** change the MongoDB image, Secrets, Pod labels, Python backend
Service selector, or restart the healthy MongoDB Pod.

## Notes

- The main student path uses namespace-scoped MCP read/write tools and actual tool approval; console/CLI recovery is fallback only.
- Run the scenario with two fresh student accounts before release.
- Tenant quotas include Argo CD and Gitea; do not add a restrictive namespace
  quota in Module 1.
