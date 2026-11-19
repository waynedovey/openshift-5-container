# Module 1 instructor preflight: MongoDB Service port

Students deploy the National Parks frontend, Python API and MongoDB 8.
**Intentional fault:** MongoDB listens on port `27017`, but its Service
forwards to `targetPort: 27018`. The MongoDB Pod can be Ready while the API
cannot connect. Students use OpenShift Lightspeed 2.0.1+ Troubleshooting to diagnose the
fault with one short, focused question. Backend logs verify that MCP
approval requests and approved decisions can occur, but the student must
still inspect and approve the proposed change in the console. If no real
approval control appears, they must use the one-field manual recovery.
An updated Service alone does **not** establish that a person approved it.

## Target delivery time

**25–30 minutes** for the console-first student lab, with a **28-minute**
guided walkthrough: project 1, frontend/RBAC 5, Python backend build 5,
MongoDB fault 6, Lightspeed diagnosis 4, verified repair 3,
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
   Deployment. The operator-managed MCP ConfigMap should contain both
   `read_only = false` and `disable_destructive = false`, and tool discovery
   should offer `resources_get` and `resources_create_or_update`.
8. Verify the generated `olsconfig` contains `tools_approval.approval_type:
   tool_annotations`. **Before permitting student AI writes, prove that an
   actual `approval_required` event is emitted and the student explicitly
   approves it**. Audit events `approval.requested` and `approval.decision`
   can help confirm what happened; an English sentence saying "I request
   approval" is not a substitute. If approval is not functioning, switch the
   whole class to manual recovery and investigate separately.
9. Keep tool-result inspection enabled. One RHOAI/vLLM Qwen3 test produced
   a `data_exfiltration` false positive reading an ordinary ConfigMap, and
   repeated broad troubleshooting queries were similarly rejected. Use
   the focused two-resource diagnosis instead; never disable guardrails
   or grant cluster-wide RBAC to students.

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

Keep the **student instructions short**. The names and exact technical safeguards
below are for instructor preparation, not for students to paste into Lightspeed.

### Mission 4 — investigate

Student prompt:

```text
My National Parks app cannot load park data.
In {user}-demo, compare only the mongodb-nationalparks Service and Deployment
using resources_get. What's wrong? Don't change anything.
```

Why this scope matters: Qwen3 repeatedly flagged one result from a broad
Pods/Services/logs investigation as `data_exfiltration` and stopped the
conversation. The two-resource `resources_get` investigation worked for
`user-clcvz-demo` and correctly identified `27018` versus `27017`. Do
not present that as a fix to the classifier itself; it is a reproducible,
lower-noise workaround. A named `targetPort: mongodb` is also valid because
the MongoDB container exposes a port named `mongodb` on `27017`.

### Mission 5 — repair

Student prompt:

```text
Use resources_create_or_update to fix only the mongodb-nationalparks
Service in {user}-demo: set targetPort to 27017; keep all else unchanged.
Submit the tool call for my approval. Don't bypass approval.
Verify the Service after the approved change.
```

Instructor acceptance criteria:
1. Before the AI request, verify `Service/mongodb-nationalparks` in that
   student's `{user}-demo` namespace has numeric `targetPort: 27018`.
2. Lightspeed should read the complete Service and use
   `resources_create_or_update` with the **full desired manifest**. The
   intended change is only `spec.ports[0].targetPort: 27018 -> 27017`;
   preserve labels, annotations, selectors, cluster IPs and other fields.
3. To count as an **approved** AI repair, the student must see a separate
   approval control for that exact tool call and explicitly approve it. The
   configured strategy `tool_annotations` and the tool's destructive hint
   alone are not evidence that an approval was requested or received.
4. Verify independently from the student terminal:

   ```bash
   oc get svc mongodb-nationalparks -n user-<guid>-demo \
     -o jsonpath='{.spec.ports[0].port}{" -> "}{.spec.ports[0].targetPort}{"\n"}'
   ```

   Expected: `27017 -> 27017`. The Service state proves the port is correct
   **at the time of the check**, not who made the change or whether the
   approval UI worked.
5. If Lightspeed says approval is unavailable, **do not instruct it to proceed
   anyway**. If the Service changes despite the student never approving a
   tool request, record this as an unresolved approval-flow issue, stop
   further AI writes for the class, and investigate audit evidence. Use
   supported administrator-managed controls to restrict MCP write exposure
   until approval is verified; *prompts are not an access-control boundary*.
6. Use the console *Networking* → *Services* → `mongodb-nationalparks` →
   *YAML* → *Edit* to set only the target port, or use the scoped student
   fallback:

   ```bash
   oc patch svc mongodb-nationalparks -n user-<guid>-demo \
     --type=json \
     -p='[{"op":"replace","path":"/spec/ports/0/targetPort","value":27017}]'
   ```

   Record whether the final repair happened through an observed approval UI,
   through manual intervention, or by an **unverified actor**; do not infer
   approval from Lightspeed's success message.

### How to investigate missing approval

The Lightspeed service code emits an `approval_required` event when a
streaming tool invocation requires approval, and audit span events named
`approval.requested` and `approval.decision`. Inspect the specific request
trace and timestamps; confirm the requested tool was `resources_create_or_update`
and the decision was `approved` before presenting this as a successful
human-in-the-loop demo. If no approval event is recorded despite an update,
investigate the tool annotations, running configuration, client transport and
write path before admitting students to that exercise.

For a **first-pass** log search as cluster administrator:

```bash
oc logs deployment/lightspeed-app-server -n openshift-lightspeed \
  --all-containers=true --since=30m \
  | grep -E 'approval\\.requested|approval\\.decision|approval_required|resources_create_or_update'
```

The filtered log output may be incomplete; correlate with your actual audit
collector or trace backend. Avoid distributing raw DEBUG traces, which may
include cluster data or user prompts.

Keep tool-result inspection enabled. Do **not** widen student RBAC, change
Secrets or Deployments, disable guardrails, or modify Argo CD/Gitea resources.

### Live rehearsal evidence

- **12 November 2026**, `user-6k7ww-demo`: Lightspeed read the MongoDB
  resources and correctly diagnosed the port mismatch.
- **19 November 2026**, `user-dpfvh-demo`: Lightspeed claimed a Service
  write and the student confirmed `27017 -> 27017`; the supplied transcript
  did not demonstrate a separate approval UI.
- **19 November 2026**, `user-clcvz-demo`: broad troubleshooting returned
  `data_exfiltration` tool-result safety alerts, while the focused
  Service/Deployment read successfully diagnosed `27018` versus `27017`.
  In the longer repair request at **01:30:30 UTC**, the **backend really
  emitted** an `approval_required` SSE event for
  `resources_create_or_update` with `destructiveHint: true` and a full
  `Service/mongodb-nationalparks` manifest containing `targetPort: 27017`.
  The same tool call's audit span recorded `approval.requested` followed
  by `approval.decision` with **`decision=approved`** at **01:30:32 UTC**,
  before the MCP `tools/call` request. MCP then reported successful
  Service update, `kubernetes-mcp-server` as a managedFields manager,
  and the correct target port. **This confirms the backend approval gate
  ran and received an approved decision.**
  The available trace does not establish whether the user visibly clicked
  Approve, or which client-side interaction supplied the authenticated
  approval decision. Inspect the console UI and decision endpoint before
  calling this an independently validated *human* approval.
  In a separate later short-prompt attempt at **01:41 UTC**, the model
  replied with a textual request to type `APPROVE` instead of invoking
  the tool. That was a **model tool-selection failure**, not proof that
  backend tool approval is unavailable. The shorter student repair prompt
  now explicitly names `resources_create_or_update` to encourage the
  real tool call; this still requires a fresh UI rehearsal.

Before class, rehearse with two fresh student accounts, verify what appears
in the actual console, and capture a genuine approval screenshot only when
such an approval really occurs. Keep the older screenshots as the manual
recovery examples, not as evidence that MCP approval was exercised.

## Notes

- The student prompts are brief. Focused MCP read-only diagnosis is mandatory; the MCP write is conditional on observed approval, otherwise manual repair is the required recovery.
- Run the scenario with two fresh student accounts before release.
- Tenant quotas include Argo CD and Gitea; do not add a restrictive namespace
  quota in Module 1.
