#!/usr/bin/env bash
# Fast-forward a student's Modules 1 and 2 to the healthy Module 3 baseline.
# Module 1 is provisioned from the corrected full-stack manifests, not by
# replaying the console UI missions. Module 2 remains owned by student Gitea.
set -euo pipefail

PROGRAM="${0##*/}"
SOURCE_URL="${SOURCE_URL:-https://github.com/rhpds/openshift-5-container.git}"
SOURCE_REF="${SOURCE_REF:-main}"
SYNC_GITEA=false
RESUME_DEMO=false
ONLY_DEMO=false
ONLY_GITOPS=false
INSECURE_TLS=false
KEEP_WORKDIR=false
WORKDIR=""

usage() {
  cat <<'HELP'
Prepare a healthy National Parks baseline for Module 3 onward as the assigned
student (user-<guid>). No instructor, cluster-admin or namespace creation.

Usage: bash prepare-module03-baseline.sh [options]

Options:
  --sync-gitea       Restore the canonical Module 2 Kustomize/manifests
                     in your OWN Gitea main; commits/pushes when they differ.
                     Without this option, a stale student repo is a hard stop.
                     Git may ask for your Gitea credentials on push.
  --resume-demo      Apply again if Module 1 in -demo is only partially present.
                     Preserves existing Secrets and PVCs; never deletes data.
  --only-demo        Prepare/check original -demo app, skip GitOps deployment.
  --only-gitops      Prepare/check Gitea and -gitops app, skip original app.
  --insecure-tls     Use curl -k for lab Routes with self-signed TLS only.
  --keep-workdir     Keep temporary source checkout for debugging.
  --help             Show this help.

Environment:
  SOURCE_URL         Canonical public GitHub source (default rhpds fork main).
  SOURCE_REF         Reference/branch to clone (default main).
  GITEA_TOKEN        Optional Gitea token/password for a non-interactive push.
  GITEA_USERNAME     Defaults to the current user-<guid> identity.

Safety: This script NEVER deletes a namespace, PVC or Secret, never force
pushes, and does not change cluster-wide quota, RBAC, Agentic Runs or policies.
It only edits student Gitea when --sync-gitea is given. It does not inject
Module 3's deliberate readiness fault; it leaves both apps healthy.
HELP
}

log() { printf '[baseline] %s\n' "$*"; }
die() { printf '\n[baseline] ERROR: %s\n' "$*" >&2; exit 1; }

while (($#)); do
  case "$1" in
    --sync-gitea) SYNC_GITEA=true ;;
    --resume-demo) RESUME_DEMO=true ;;
    --only-demo) ONLY_DEMO=true ;;
    --only-gitops) ONLY_GITOPS=true ;;
    --insecure-tls) INSECURE_TLS=true ;;
    --keep-workdir) KEEP_WORKDIR=true ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; die "Unknown argument: $1" ;;
  esac
  shift
done
[[ "$ONLY_DEMO" == true && "$ONLY_GITOPS" == true ]] && die 'Choose only one of --only-demo or --only-gitops.'

for tool in oc git curl python3 mktemp awk; do
  command -v "$tool" >/dev/null 2>&1 || die "Missing required command: $tool"
done

STUDENT="$(oc whoami 2>/dev/null)" || die 'Log in with oc as your assigned user-<guid> first.'
[[ "$STUDENT" =~ ^user-[a-z0-9]+(-[a-z0-9]+)*$ ]] || die "Refusing identity '$STUDENT'. Sign in as your lab student, not an administrator or Showroom account."
DEMO_NS="${STUDENT}-demo"
GITOPS_NS="${STUDENT}-gitops"
GITEA_USERNAME="${GITEA_USERNAME:-$STUDENT}"
APPLICATION=national-parks-settings

for ns in "$DEMO_NS" "$GITOPS_NS"; do
  oc get namespace "$ns" -o name >/dev/null 2>&1 || die "Cannot see pre-provisioned namespace '$ns'. Contact instructor; do not create it."
done

WORKDIR="$(mktemp -d)"
cleanup() {
  if [[ "$KEEP_WORKDIR" == true ]]; then
    printf '\n[baseline] Temporary source: %s\n' "$WORKDIR"
  else
    rm -rf -- "$WORKDIR"
  fi
}
trap cleanup EXIT

log "Signed in as $STUDENT; namespaces: $DEMO_NS / $GITOPS_NS"
log "Fetching known-good manifests from $SOURCE_URL ($SOURCE_REF)"
git -c credential.helper= clone --quiet --depth 1 --single-branch --branch "$SOURCE_REF" \
  "$SOURCE_URL" "$WORKDIR/reference" || die 'Could not clone public reference repository.'

MANIFESTS="$WORKDIR/reference/content/modules/ROOT/examples/module02-gitops"
[[ -f "$MANIFESTS/kustomization.yaml" && -d "$MANIFESTS/fullstack" ]] || die 'Reference has no Module 2 full-stack Kustomization.'
# Fail safely on old/incorrect source instead of recreating known previous bugs.
[[ $(grep -Ec '^[[:space:]]*-[[:space:]]+fullstack[[:space:]]*$' "$MANIFESTS/kustomization.yaml") -eq 1 ]] || die 'Reference root does not select fullstack.'
[[ $(grep -Ec 'argocd.argoproj.io/sync-wave: "0"' "$MANIFESTS/fullstack/01-mongodb.yaml") -ge 2 ]] || die 'Reference PVC/Deployment wave 0 correction missing.'
[[ $(grep -Ec 'argocd.argoproj.io/sync-wave: "2"' "$MANIFESTS/fullstack/04-parksmap-frontend.yaml") -ge 1 ]] || die 'Reference ParksMap wave 2 correction missing.'
[[ $(grep -Ec 'port: http' "$MANIFESTS/fullstack/04-parksmap-frontend.yaml") -ge 1 ]] || die 'Reference ParksMap readiness probe is not baseline healthy.'

# Only the Kustomize source files are synchronized to Gitea: not Secrets or
# arbitrary user repository content (source, notes, test exercises, etc.).
SOURCE_FILES=(
  kustomization.yaml
  fullstack/kustomization.yaml
  fullstack/national-parks-gitops-info.yaml
  fullstack/00-mongodb-credentials.yaml
  fullstack/01-mongodb.yaml
  fullstack/02-nationalparks-backend.yaml
  fullstack/03-parksmap-discovery.yaml
  fullstack/04-parksmap-frontend.yaml
  fullstack/05-park-data-bootstrap.yaml
)

get_deploy_ready() {
  local ns="$1" name="$2" state
  state="$(oc get deployment "$name" -n "$ns" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true)"
  [[ "$state" == '1' ]]
}

count_demo_deploys() {
  local name present=0
  for name in mongodb-nationalparks nationalparks parksmap; do
    if oc get deployment "$name" -n "$DEMO_NS" -o name >/dev/null 2>&1; then
      present=$((present + 1))
    fi
  done
  printf '%s' "$present"
}

print_diagnostics() {
  local ns="$1"
  printf '\n[baseline] Diagnostics for %s:\n' "$ns" >&2
  oc get deployments,pods,pvc,jobs,buildconfig,builds -n "$ns" >&2 || true
  oc get events -n "$ns" --sort-by=.lastTimestamp 2>/dev/null | tail -20 >&2 || true
}

wait_rollout() {
  local ns="$1" name="$2" timeout="${3:-600s}"
  if ! oc rollout status "deployment/$name" -n "$ns" --timeout="$timeout"; then
    print_diagnostics "$ns"
    die "Deployment $ns/$name did not roll out."
  fi
}

curl_flags=(-fsS --connect-timeout 5 --max-time 20)
if [[ "$INSECURE_TLS" == true ]]; then curl_flags+=(-k); fi

route_host() {
  oc get route "$2" -n "$1" -o jsonpath='{.spec.host}' 2>/dev/null
}

ensure_park_data() {
  local ns="$1" api_host raw count
  api_host="$(route_host "$ns" national-parks-app)" || die "Cannot read National Parks Route in $ns"
  [[ -n "$api_host" ]] || die "Missing National Parks Route host in $ns"
  raw="$(curl "${curl_flags[@]}" "https://$api_host/ws/data/all")" || die "Backend data endpoint failed in $ns"
  count="$(printf '%s' "$raw" | python3 -c 'import json,sys; x=json.load(sys.stdin); assert isinstance(x,list), "Expected JSON list of parks"; print(len(x))')" || die "Unexpected park data JSON in $ns"
  if [[ "$count" == 0 ]]; then
    log "Database is empty in $ns; loading sample parks exactly once."
    curl "${curl_flags[@]}" --max-time 130 "https://$api_host/ws/data/load" >/dev/null || die "Park data loader failed in $ns"
    raw="$(curl "${curl_flags[@]}" "https://$api_host/ws/data/all")" || die "Cannot recheck park data in $ns"
    count="$(printf '%s' "$raw" | python3 -c 'import json,sys; x=json.load(sys.stdin); assert isinstance(x,list), "Expected JSON list"; print(len(x))')" || die "Invalid park data after loading."
  fi
  [[ "$count" -gt 0 ]] || die "Park list is still empty in $ns"
  log "$ns has $count park records."
}

verify_namespace() {
  local ns="$1" name map_host code
  for name in mongodb-nationalparks nationalparks parksmap; do
    get_deploy_ready "$ns" "$name" || { print_diagnostics "$ns"; die "Expected $ns/$name 1/1 Ready."; }
  done
  ensure_park_data "$ns"
  map_host="$(route_host "$ns" parksmap)" || die "Missing ParksMap Route in $ns"
  [[ -n "$map_host" ]] || die "Missing ParksMap Route host in $ns"
  code="$(curl "${curl_flags[@]}" -o /dev/null -w '%{http_code}' \
    "https://$map_host/" 2>/dev/null || true)"
  [[ "$code" == '200' ]] || die "ParksMap route $ns returned HTTP ${code:-unavailable}, expected 200."
  local backend_list
  backend_list="$(curl "${curl_flags[@]}" "https://$map_host/ws/backends/list")" \
    || die "ParksMap backend discovery endpoint failed in $ns"
  [[ "$backend_list" == *nationalparks* ]] \
    || die "ParksMap is reachable, but it did not discover the nationalparks backend in $ns. Check discovery RBAC and Service labels."
  log "PASS: $ns — three deployments Ready, parks data present, map backend discovered, HTTP 200."
}

# Fullstack's ordered files are applied directly to the original -demo project.
# This is a HEALTHY equivalent, not a replay of Module 1's broken Service step.
prepare_demo() {
  local count name broken_port
  count="$(count_demo_deploys)"
  if [[ "$count" == 3 ]]; then
    log "Existing Module 1 deployments found in $DEMO_NS; preserving them."
    # Only repair the well-known Module 1 training fault when it is present.
    broken_port="$(oc get svc mongodb-nationalparks -n "$DEMO_NS" -o jsonpath='{.spec.ports[0].targetPort}' 2>/dev/null || true)"
    if [[ "$broken_port" == '27018' ]]; then
      log "Repairing the original Module 1 demo Service targetPort 27018 -> 27017."
      oc patch svc mongodb-nationalparks -n "$DEMO_NS" --type=merge \
        -p '{"spec":{"ports":[{"name":"mongodb","port":27017,"protocol":"TCP","targetPort":27017}]}}' >/dev/null
    fi
    if [[ "$broken_port" != '27018' && "$broken_port" != '27017' && "$broken_port" != 'mongodb' ]]; then
      die "Unexpected MongoDB Service targetPort '${broken_port:-missing}' in $DEMO_NS. Refusing to patch it."
    fi
    # Module 1 may already be healthy but still require its one-time data load.
    verify_namespace "$DEMO_NS"
    return
  fi
  if [[ "$count" != 0 && "$RESUME_DEMO" != true ]]; then
    die "Partial Module 1 install ($count/3 Deployments). Review existing resources; retry with --resume-demo to apply canonical manifests without deleting data."
  fi
  if [[ "$count" == 0 ]]; then
    for name in mongodb-nationalparks nationalparks parksmap; do
      if oc get svc "$name" -n "$DEMO_NS" -o name >/dev/null 2>&1; then
        [[ "$RESUME_DEMO" == true ]] || die "Service $DEMO_NS/$name already exists. Use --resume-demo only if it belongs to this lab."
      fi
    done
  fi
  [[ "$(oc auth can-i create deployments.apps -n "$DEMO_NS")" == yes ]] || die "Student cannot create Deployments in $DEMO_NS. Instructor must grant normal lab edit permissions."
  log "Deploying healthy Module 1 equivalent into $DEMO_NS in dependency order."
  # Wait for generated credentials before MongoDB; no password enters source.
  oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/00-mongodb-credentials.yaml"
  oc wait -n "$DEMO_NS" --for=condition=complete job/nationalparks-credentials-bootstrap --timeout=360s \
    || { print_diagnostics "$DEMO_NS"; die 'MongoDB credentials Job did not complete.'; }
  oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/01-mongodb.yaml"
  wait_rollout "$DEMO_NS" mongodb-nationalparks 600s
  oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/02-nationalparks-backend.yaml"
  wait_rollout "$DEMO_NS" nationalparks 900s
  oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/03-parksmap-discovery.yaml"
  oc apply -n "$DEMO_NS" -f "$MANIFESTS/fullstack/04-parksmap-frontend.yaml"
  wait_rollout "$DEMO_NS" parksmap 600s
  # Omit the GitOps PostSync Job in the plain Module 1 project. Safely load
  # sample data only if empty after the API becomes healthy.
  verify_namespace "$DEMO_NS"
}

find_gitea_url() {
  local route host
  route="$(oc get gitea gitea -n "$DEMO_NS" -o jsonpath='{.status.giteaRoute}' 2>/dev/null || true)"
  if [[ -z "$route" ]]; then
    host="$(oc get routes -n "$DEMO_NS" \
      -o jsonpath='{range .items[*]}{.spec.host}{"\n"}{end}' 2>/dev/null \
      | awk '/^gitea-/ { print; exit }')"
    route="$host"
  fi
  [[ -n "$route" ]] || die "Cannot discover student Gitea Route in $DEMO_NS"
  route="${route%/}"
  case "$route" in
    https://*) GITEA_BASE="$route" ;;
    http://*) die "Refusing plaintext Gitea Route: $route" ;;
    *) GITEA_BASE="https://$route" ;;
  esac
  # No credentials are added to a remote URL.
  GITEA_REPO="$GITEA_BASE/$STUDENT/openshift-5-container.git"
}

sync_or_verify_gitea() {
  local file count=0 checkout="$WORKDIR/student-gitea"
  find_gitea_url
  log "Checking public student Gitea main: $GITEA_REPO"
  git -c credential.helper= clone --quiet --branch main --single-branch -- \
    "$GITEA_REPO" "$checkout" || die 'Cannot clone student Gitea repository. Verify it exists and is public.'
  for file in "${SOURCE_FILES[@]}"; do
    # Module 2 deliberately lets students personalize this ConfigMap; its
    # content need not match, but the file must exist and be nonempty.
    if [[ "$file" == 'fullstack/national-parks-gitops-info.yaml' ]] \
       && [[ -s "$checkout/content/modules/ROOT/examples/module02-gitops/$file" ]]; then
      continue
    fi
    if [[ ! -f "$checkout/content/modules/ROOT/examples/module02-gitops/$file" ]] \
       || ! git diff --no-index --quiet -- "$MANIFESTS/$file" "$checkout/content/modules/ROOT/examples/module02-gitops/$file"; then
      count=$((count + 1))
      log "Source difference: $file"
    fi
  done
  if [[ "$count" -eq 0 ]]; then
    log "Student Gitea source has all required working Module 2 Kustomize/manifest files."
    return
  fi
  if [[ "$SYNC_GITEA" != true ]]; then
    die "$count Module 2 source file(s) differ from upstream. To restore the healthy baseline in your own Gitea main, rerun with --sync-gitea. No Gitea content was changed."
  fi
  log "--sync-gitea: restoring $count differing Module 2 files (not other student files)."
  for file in "${SOURCE_FILES[@]}"; do
    destination="$checkout/content/modules/ROOT/examples/module02-gitops/$file"
    # Preserve the student's harmless Module 2 checkpoint message if present.
    if [[ "$file" == 'fullstack/national-parks-gitops-info.yaml' && -s "$destination" ]]; then
      continue
    fi
    mkdir -p "$(dirname "$destination")"
    cp "$MANIFESTS/$file" "$destination"
  done
  (
    cd "$checkout"
    git add -- content/modules/ROOT/examples/module02-gitops
    git diff --cached --check
    if git diff --cached --quiet; then exit 0; fi
    git -c user.name="$STUDENT (workshop bootstrap)" \
        -c user.email="$STUDENT@users.noreply.invalid" \
        commit --quiet -m 'bootstrap: restore healthy Module 2 source for later labs'
    if [[ -n "${GITEA_TOKEN:-}" ]]; then
      cat > "$WORKDIR/git-askpass" <<'ASKPASS'
#!/usr/bin/env bash
case "${1:-}" in
  *Username*) printf '%s\n' "$GITEA_USERNAME" ;;
  *Password*) printf '%s\n' "$GITEA_TOKEN" ;;
  *) exit 1 ;;
esac
ASKPASS
      chmod 700 "$WORKDIR/git-askpass"
      GIT_ASKPASS="$WORKDIR/git-askpass" GIT_TERMINAL_PROMPT=0 \
        git -c credential.helper= push origin main \
        || die 'Gitea push failed; fix credentials or concurrent changes; no force push was attempted.'
    else
      git push origin main || die 'Gitea push failed; authenticate with your account/password or Gitea token.'
    fi
  )
  log 'Healthy full-stack GitOps source committed to student Gitea main.'
}

apply_gitops_application() {
  local actual url target
  if oc get application "$APPLICATION" -n "$DEMO_NS" -o name >/dev/null 2>&1; then
    url="$(oc get application "$APPLICATION" -n "$DEMO_NS" -o jsonpath='{.spec.source.repoURL}')"
    target="$(oc get application "$APPLICATION" -n "$DEMO_NS" -o jsonpath='{.spec.destination.namespace}')"
    [[ "$url" == "$GITEA_REPO" && "$target" == "$GITOPS_NS" ]] \
      || die "Existing $APPLICATION points to unexpected Gitea/destination ($url -> $target). Refusing to replace it."
  fi
  log "Ensuring Argo CD Application $DEMO_NS/$APPLICATION deploys to $GITOPS_NS."
  cat <<YAML | oc apply -n "$DEMO_NS" -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: $APPLICATION
  namespace: $DEMO_NS
spec:
  project: default
  source:
    repoURL: $GITEA_REPO
    targetRevision: main
    path: content/modules/ROOT/examples/module02-gitops
  destination:
    server: https://kubernetes.default.svc
    namespace: $GITOPS_NS
  ignoreDifferences:
    - group: apps
      kind: Deployment
      name: nationalparks
      jsonPointers:
        - /spec/template/spec/containers/0/image
  syncPolicy:
    automated:
      enabled: true
      prune: false
      selfHeal: true
    syncOptions:
      - RespectIgnoreDifferences=true
    retry:
      limit: 5
      backoff:
        duration: 10s
        factor: 2
        maxDuration: 2m
YAML
}

wait_gitops() {
  local out status health phase revision tries
  for ((tries=1; tries<=48; tries++)); do
    out="$(oc get application "$APPLICATION" -n "$DEMO_NS" -o json 2>/dev/null \
      | python3 -c 'import json,sys; o=json.load(sys.stdin); s=o.get("status",{}); print("|".join([s.get("sync",{}).get("status","Unknown"),s.get("health",{}).get("status","Unknown"),s.get("operationState",{}).get("phase","None"),s.get("sync",{}).get("revision","")]))' \
      || true)"
    IFS='|' read -r status health phase revision <<<"$out"
    if [[ "$status" == Synced && "$health" == Healthy ]]; then
      log "Argo CD $APPLICATION: Synced / Healthy (revision ${revision:0:12})."
      return
    fi
    if ((tries == 1 || tries % 4 == 0)); then
      log "Argo CD: ${status:-Unknown} / ${health:-Unknown}, operation ${phase:-Unknown}; polling..."
    fi
    if [[ "$phase" == Failed || "$phase" == Error ]]; then
      oc get application "$APPLICATION" -n "$DEMO_NS" -o json \
        | python3 -c 'import json,sys; s=json.load(sys.stdin).get("status",{}); print("Operation message:",s.get("operationState",{}).get("message","not reported"))' || true
      die 'Argo CD sync failed. Inspect Application events and Gitea revision; do not delete PVCs or Secrets.'
    fi
    sleep 15
  done
  print_diagnostics "$GITOPS_NS"
  oc get application "$APPLICATION" -n "$DEMO_NS" -o yaml | tail -80 >&2 || true
  die 'Argo CD did not become Synced / Healthy within the configured polling limit.'
}

preflight_gitops() {
  [[ "$(oc auth can-i create applications.argoproj.io -n "$DEMO_NS")" == yes ]] \
    || { oc get application "$APPLICATION" -n "$DEMO_NS" -o name >/dev/null 2>&1 \
      || die "Student cannot create Argo CD Applications in $DEMO_NS. Ask instructor to grant the intended project permissions."; }
  sync_or_verify_gitea
}

prepare_gitops() {
  apply_gitops_application
  # A hard refresh updates Git's desired revision. It does not terminate
  # an already-running sync operation; the script deliberately never does.
  oc annotate application "$APPLICATION" -n "$DEMO_NS" \
    argocd.argoproj.io/refresh=hard --overwrite >/dev/null || true
  wait_gitops
  verify_namespace "$GITOPS_NS"
}

# Verify the imported Gitea source before modifying either application.
if [[ "$ONLY_DEMO" != true ]]; then preflight_gitops; fi
if [[ "$ONLY_GITOPS" != true ]]; then prepare_demo; fi
if [[ "$ONLY_DEMO" != true ]]; then prepare_gitops; fi

printf '\n============================================================\n'
if [[ "$ONLY_DEMO" == true ]]; then
  printf 'PARTIAL BASELINE — only Module 1 app checked for %s\n' "$STUDENT"
elif [[ "$ONLY_GITOPS" == true ]]; then
  printf 'PARTIAL BASELINE — only Module 2 app checked for %s\n' "$STUDENT"
else
  printf 'MODULE 3 BASELINE READY — %s\n' "$STUDENT"
fi
printf 'Original:  %s\n' "$DEMO_NS"
printf 'GitOps:    %s\n' "$GITOPS_NS"
printf 'Argo CD:   %s/%s\n' "$DEMO_NS" "$APPLICATION"
printf 'Gitea:     %s\n' "${GITEA_REPO:-not checked (--only-demo)}"
printf '============================================================\n'
if [[ "$ONLY_DEMO" == true || "$ONLY_GITOPS" == true ]]; then
  printf 'Run again without --only-* before starting Module 3 to verify BOTH apps.\n'
else
  printf 'You can start Module 3 without redoing the Module 1/2 UI exercises.\n'
fi
