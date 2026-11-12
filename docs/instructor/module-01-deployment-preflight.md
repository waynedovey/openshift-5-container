# Module 1 instructor preflight: MongoDB Service port

Students deploy the National Parks frontend, Python API and MongoDB 8.
**Intentional fault:** MongoDB listens on port `27017`, but its Service
forwards to `targetPort: 27018`. The MongoDB Pod can be Ready while the API
cannot connect. Students use Lightspeed 2.0 for read-only investigation and
repair the MongoDB Service manually.

## Before class

1. Authenticate the Showroom terminal as the assigned student, **not** the
   Showroom ServiceAccount. Verify `oc whoami` returns `user-<guid>`.
2. Ensure the student can patch or edit Services in `user-<guid>-demo`.
   Do not grant broad permissions to the Showroom ServiceAccount.
3. Ensure the `parksmap-discovery` ServiceAccount, Role and RoleBinding exist.
   The `parksmap` Deployment must use that ServiceAccount.
4. Confirm the frontend image pulls, Python backend builds, and
   `quay.io/mongodb/mongodb-community-server:8.0.32-ubi9-slim` starts.
5. Check the database Secret exists, with five correct keys, and the Python
   backend uses `envFrom.secretRef.name: nationalparks-mongodb-parameters`.
   Do not expose credentials.
6. Ensure Argo CD auto-sync will not overwrite student-created National Parks
   resources; leave pre-provisioned Argo CD and Gitea workloads alone.

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

Have a fresh student run Mission 4's short read-only prompt. Check whether
Lightspeed identifies the port mismatch from live Services, Pods,
EndpointSlices and backend logs. **This new scenario is not yet validated
against Lightspeed 2.0.**

In Mission 5, students use the console to change **only**
`mongodb-nationalparks` Service `spec.ports[0].targetPort` to `27017`.

Verify in the student terminal:

```bash
oc get svc mongodb-nationalparks -n user-<guid>-demo \
  -o jsonpath='{.spec.ports[0].port}{" -> "}{.spec.ports[0].targetPort}{"\n"}'
```

Expected: `27017 -> 27017`. Then load disposable park data **once** via
`/ws/data/load`, verify `/ws/data/all` contains records, and open ParksMap
to confirm markers appear.

**Do not** change the MongoDB image, Secrets, Pod labels, Python backend
Service selector, or restart the healthy MongoDB Pod.

## Notes

- The lab uses live Kubernetes read tools; MCP write tools are not required.
- Run the scenario with two fresh student accounts before release.
- Tenant quotas include Argo CD and Gitea; do not add a restrictive namespace
  quota in Module 1.
