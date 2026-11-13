> **Permanent operator patch:** The tested-against-source unified diff lives at
> [`patches/gitea-operator/0001-reconcile-changed-repositories.patch`](../../patches/gitea-operator/0001-reconcile-changed-repositories.patch).
> See [application and rollout instructions](../../patches/gitea-operator/README.md).
> The patch is **not deployed** until the RHPDS Gitea Operator maintainers
> merge and release it. Continue using the selective workshop backfill helper
> on existing clusters until the operator version is upgraded.

# Gitea repository migration for existing workshop students

## Cause

The RHPDS Gitea Operator guards all repository migration with the one-time
Gitea.status.repoMigrationComplete flag. When initial provisioning imports
only openshift-starter-guides, that flag becomes true. Adding
openshift-5-container to automation/gitops/bootstrap-tenant/values.yaml
updates the CR spec but does NOT check/import missing repositories again.

This was reproduced on user-6k7ww-demo. Resetting status alone did not
reconcile. Resetting status and toggling spec.giteaMigrateRepositories
false/true triggered an Ansible playbook run that checked both repos,
imported the missing one and returned HTTP 200; status became true.

## Safe workaround for an existing namespace

Dry run (no writes):

~~~bash
bash automation/scripts/reconcile-gitea-repositories.sh -n user-6k7ww-demo
~~~

Backfill only when the dry run identifies missing repos:

~~~bash
bash automation/scripts/reconcile-gitea-repositories.sh -n user-6k7ww-demo --apply
~~~

Requires oc, jq, curl and an admin/instructor identity with patch permission
for giteas and giteas/status. Only PUBLIC repos with one generated user
are supported. The command reads the Gitea CR but does not print the
admin password or tokens. Do not delete Gitea, PostgreSQL, or PVCs.
Avoid applying this automatically across all student namespaces.

The helper only patches when a repository is missing, triggers the operator,
then checks both live repo availability and the migration completion status.
In a cluster where GitOps self-heals the Gitea CR, check for conflicts
during the brief spec toggle.

## Permanent code fix: RHPDS Gitea Operator

See the complete [`main.yml` patch](../../patches/gitea-operator/0001-reconcile-changed-repositories.patch).

It calculates a fingerprint from the desired repository list and compares
that value with the last *successfully migrated* fingerprint stored in
`status.repoMigrationConfigHash`. A changed list (or an incomplete
migration) triggers the existing per-repository GET-before-POST import tasks.
It marks migration incomplete while processing and records the new hash
alongside `repoMigrationComplete: true` **only after all imports succeed**.
Existing repos are skipped. This also supports upgrading older Gitea CRs
that don't yet have `repoMigrationConfigHash`.

The operator code must be built and released through its OLM pipeline.
The workshop Helm values already list both repos; changing those values
alone won't fix an existing operator. Confirm import via Gitea's API after
operator rollout. This reconciles *list changes*; restoring deleted repos
without changing the list would require separate periodic drift detection.

## Validate

~~~bash
NS=user-6k7ww-demo
GITEA_URL=$(oc get gitea gitea -n "$NS" -o jsonpath='{.status.giteaRoute}')
OWNER=$(oc get gitea gitea -n "$NS" -o jsonpath='{.spec.giteaGenerateUserFormat}')

curl -sS -o /dev/null -w 'HTTP %{http_code}\n' \
  "$GITEA_URL/api/v1/repos/$OWNER/openshift-5-container"
oc get gitea gitea -n "$NS" \
  -o jsonpath='{.status.repoMigrationComplete}{"\n"}'
~~~

Expected: HTTP 200 and true. Then confirm student can edit
content/modules/ROOT/examples/module02-gitops/national-parks-gitops-info.yaml.
