# Permanent fix for incremental Gitea repository migration

The workshop bootstrap already provisions both `openshift-starter-guides` and `openshift-5-container`. The remaining bug belongs in the separately deployed [RHPDS Gitea Operator](https://github.com/rhpds/gitea-operator), not the Helm values.

## Apply the operator patch

The patch `patches/gitea-operator/0001-reconcile-changed-repositories.patch` was generated against `rhpds/gitea-operator:main`, at file SHA `b3fa9354e313bea69ffea26bf8cb3c5cde535fab`.

```bash
git clone https://github.com/rhpds/gitea-operator.git
cd gitea-operator
git switch -c fix/reconcile-changed-gitea-repositories

git apply --check /path/to/openshift-5-container/patches/gitea-operator/0001-reconcile-changed-repositories.patch
git apply /path/to/openshift-5-container/patches/gitea-operator/0001-reconcile-changed-repositories.patch
git diff --check
git diff -- roles/gitea-ocp/tasks/main.yml
```

Open a PR against `rhpds/gitea-operator:main` using your own fork/branch. The connected GitHub app currently cannot create or fork this upstream operator repo.

## How the patch works

- Calculate a SHA-256 fingerprint from the configured `giteaRepositoriesList`.
- If migration is incomplete **or** the fingerprint differs from the last successful migration, run the repository checks.
- Mark `repoMigrationComplete: false` while reconciling; preserve the old fingerprint in case of failure.
- Reuse the operator's existing `migrate_repos.yml` GET-before-POST behavior, which skips repositories already present and imports new ones with `mirror:false`.
- Record the new fingerprint and `repoMigrationComplete: true` only after successful tasks.

The new field `status.repoMigrationConfigHash` is stored in the CR's status object. The current CRD supports arbitrary status fields (`x-kubernetes-preserve-unknown-fields: true`), so no CRD schema update is expected to be required.

## Upgrade and verify

**Do not patch the cluster's installed operator YAML directly.** Build/release the fixed operator through its proper RHPDS OLM/catalog pipeline, then verify rollout in the correct namespace (`openshift-operators` on the workshop cluster).

```bash
oc get deployment -n openshift-operators gitea-operator-controller-manager
oc rollout status -n openshift-operators deployment/gitea-operator-controller-manager
```

After upgrading, reconciliation of the existing Gitea CR should detect the missing fingerprint and run GET-before-POST for both repositories. If your operator deployment does not reconcile existing watched CRs automatically on startup, trigger a benign CR spec change or use the selective workshop backfill helper instead. Do not delete a Gitea, PostgreSQL, or PVC.

```bash
NS=user-6k7ww-demo
oc get gitea gitea -n "$NS" -o json | jq '{complete:.status.repoMigrationComplete,hash:.status.repoMigrationConfigHash,repoNames:[.spec.giteaRepositoriesList[].name]}'
GITEA_URL=$(oc get gitea gitea -n "$NS" -o jsonpath='{.status.giteaRoute}')
OWNER=$(oc get gitea gitea -n "$NS" -o jsonpath='{.spec.giteaGenerateUserFormat}')
curl -fsS "$GITEA_URL/api/v1/repos/$OWNER/openshift-5-container" | jq '{full_name,mirror,private}'
```

Expected: `complete=true`, a nonempty hash, and the repository owned by the student with `mirror=false`.

## Operator acceptance tests

1. Fresh tenant with two repositories: both are imported, completion true and hash set.
2. Pre-existing tenant with only starter repo, completion true and no hash: the operator rechecks and imports the missing GitOps repo.
3. Unchanged repository list: the hash matches, so subsequent normal reconciliations skip migration.
4. A new third repository: desired hash changes and only that repo is imported.
5. A failed import: completion remains false and the previous hash remains unchanged, allowing retry.
6. Pre-existing repository: never overwritten, never switched to a mirror.

This approach reconciles changes in the **desired list**. It does not by itself restore repos deleted manually while that list is unchanged; that would need periodic Gitea state checks and appropriate limits. Ensure the Gitea Operator is released before relying on this feature for existing tenants.
