# Module 1: native-console deployment screenshot guide

The 45-minute Mission National Parks uses the student's **existing** workshop
project, `{user}-demo`, using the student's provisioned `user` attribute.
Students do **not** create a new namespace. In the supplied console captures,
the project is `user-pjbsb-demo`, which matches this design.

The real OpenShift 5 screenshots for the frontend image deployment and browser
journey are uploaded as S05a–S05i. The complete Python backend Git-import,
BuildConfig, build-log, Topology, Routes and welcome-page sequence is uploaded
as S06a–S06i. S00 is also a real Projects screen. S04a–S04b capture the
**previous** two-resource MongoDB YAML import and confirmation. The current lab
adds a non-secret ConfigMap to allow a one-field MCP image replacement, so
S04a/S04b must be recaptured showing **three** created resources. Screenshots S01–S04 and
S07–S08 are still pending; the old PNGs in those slots are illustrations,
**not proof of a working end-to-end lab**.

## Capture list (use the exact filenames)

| ID | Filename | New screen to capture | Evidence or callout |
|---|---|---|---|
| S00 | `module01-s00-console.png` | Student sees `user-<GUID>-demo` in the Projects list | Existing project; no *Create Project* action |
| S01 | `module01-s01-map.png` | Populated National Parks map after the student loads data | Visible park markers and one selected park |
| S02 | `module01-s02-topology.png` | Topology showing all three newly created workloads | `parksmap`, `nationalparks`, `mongodb-nationalparks` |
| S03 | `module01-s03-route.png` | `Networking → Routes → nationalparks` | Route hostname and `type=parksmap-backend` label |
| S04 | `module01-s04-service.png` | `Networking → Services → mongodb-nationalparks` | Internal ClusterIP; no database Route |
| S04a | `module01-s04a-mongodb-yaml-editor.png` | Quick create → Import YAML | **Recapture required:** ConfigMap, Deployment with deliberately old image, and Service; uploaded capture is superseded |
| S04b | `module01-s04b-mongodb-created.png` | Import YAML → Create confirmation | **Recapture required:** three successful resources, not two; uploaded capture is superseded |
| S05a | `module01-s05a-container-images-menu.png` | OpenShift 5 top-bar `+` menu | Choose *Container images*; **uploaded** |
| S05b | `module01-s05b-image-and-project.png` | Deploy Image form | Validated `quay.io/openshiftroadshow/parksmap:latest` and `user-<GUID>-demo`; **uploaded** |
| S05c | `module01-s05c-runtime-and-app.png` | Runtime icon and General settings | Default `openshift` icon, Create application, `national-parks-app`, `parksmap`; **uploaded** |
| S05d | `module01-s05d-deployment-and-route.png` | Deploy and Advanced options | Deployment, target port `8080`, Create a route checked; **uploaded** |
| S05e | `module01-s05e-frontend-labels.png` | Frontend labels | Four exact workload labels; **uploaded** |
| S05f | `module01-s05f-topology-navigation.png` | Workloads menu with Topology selected | Student's existing project, `parksmap` and 1 Pod; **uploaded** |
| S05g | `module01-s05g-open-url.png` | Topology showing the frontend's external-link icon | Click *Open URL*; **uploaded** |
| S05h | `module01-s05h-location-permission.png` | Browser permission prompt on the new frontend Route | Explain browser geolocation is optional and the legacy denial-handling limitation; **uploaded** |
| S05i | `module01-s05i-frontend-first-open.png` | First browser tab showing the empty world map | Legacy OpenShift 4 heading is hard-coded in the frontend, not an OCP cluster version check; **uploaded** |
| S06a | `module01-s06a-git-repository.png` | Import from Git, with project and source Git URL | Correct project, Dockerfile recommended; **uploaded** |
| S06b | `module01-s06b-buildconfig-settings.png` | General and Build form | Existing application `national-parks-app`, name `nationalparks`, BuildConfig; **uploaded** |
| S06c | `module01-s06c-deployment-route.png` | Deployment form | Deployment, port `8080`, Create a route checked; **uploaded** |
| S06d | `module01-s06d-backend-labels.png` | Backend labels | Five exact labels, including `type=parksmap-backend`; **uploaded** |
| S06e | `module01-s06e-builds-navigation.png` | Console's Builds navigation | Builds → Builds; **uploaded** |
| S06f | `module01-s06f-build-success-logs.png` | Build details → Logs | Build Complete, Successfully pushed, Push successful; **uploaded** |
| S06g | `module01-s06g-topology-resources.png` | Backend Topology → Resources | Running Pod and Complete build; **uploaded** |
| S06h | `module01-s06h-backend-routes.png` | Networking → Routes | Backend Route `nationalparks` healthy alongside frontend Route; **uploaded** |
| S06i | `module01-s06i-backend-welcome.png` | Open backend Route's Location URL | `Welcome to the National Parks data service.`; **uploaded** |
| S07 | `module01-s07-lightspeed.png` | Lightspeed MCP diagnosis and approved update to MongoDB image | Real `resources_create_or_update` tool result, image `registry.redhat.io/rhmap47/mongodb` to `quay.io/mongodb/mongodb-community-server:8.0.32-ubi9-slim`, and approval evidence |
| S08 | `module01-s08-health.png` | Final health in OCP 5 console | Three ready workloads, two Routes, working map after recovery |

The earlier `module01-s05-scale-before.png` and `module01-s06-scale-after.png`
placeholders are no longer referenced in Module 1. S05a–S05i and S06a–S06i
replace those illustrative screenshots.

## How to replace a screenshot

1. Log into the actual OCP 5 workshop cluster as a **student**, not as admin.
   Select the already-provisioned `user-<GUID>-demo` project. Do not create a
   duplicate namespace or select a different student's project.
2. Capture at approximately 16:9 (ideally 1440 × 810) with sufficient console
   navigation visible for a student to reproduce the click path.
3. Use one or two small numbered callouts at most. Do not include Secret
   values, bearer tokens, passwords, kubeconfigs or unrelated customer data.
4. Save the PNG using the *exact* filename above and replace it in
   `content/modules/ROOT/images/` on your fork.
5. Check the rendered Module 1 on your fork's GitHub Pages preview before
   submitting an upstream PR.

## Acceptance before delivery

- [x] S00 shows the student's pre-existing `user-<GUID>-demo` project.
- [x] S05a–S05i show the Console navigation, validated frontend image, project,
      runtime, application name, Deployment, Route, labels, Topology, Open URL,
      browser permission and initial map.
- [x] S06a–S06i document the Dockerfile import, BuildConfig, build logs,
      running backend, Routes and HTTP welcome message. This does not
      validate MongoDB connectivity or map data.
- [ ] Recapture S04a–S04b after the three-resource import update. Existing captures
      are real but outdated and do not document bootstrap ConfigMap creation.
- [ ] Student can deploy into `user-<GUID>-demo` without modifying the existing
      Argo CD, Gitea or Showroom components in that namespace.
- [ ] The student can create frontend/BuildConfig/Route resources through the
      actual OCP 5 console and see the newly created Topology group.
- [ ] Each student creates `nationalparks-mongodb-parameters` in their **own**
      demo project using the console's key/value Secret form; both password
      values are private and different. The instructor does not pre-create it.
- [ ] The deliberately broken legacy MongoDB image starts and reports 3.2.10;
      the backend logs show an actual protocol incompatibility with PyMongo 4.18.1.
- [ ] The built-in MCP `resources_create_or_update` tool is exposed to a student
      account, obtains a human approval and changes only the MongoDB container
      image to `quay.io/mongodb/mongodb-community-server:8.0.32-ubi9-slim`.
- [ ] The modern image starts under the namespace's restricted SCC, consumes
      the student Secret and executes `mongodb-nationalparks-bootstrap` to
      create an application user without exposing credentials.
- [ ] Instructor confirms how this legacy ParksMap frontend handles denied
      browser geolocation, and provides a privacy-respecting fallback.
- [ ] The backend source build and both MongoDB image pulls were tested under
      student-level permissions and complete within the allotted time.
- [ ] The student-created Secret reference, backend Route discovery label, data load and map
      marker display all work as documented.
- [ ] Screenshots are authentic, legible and match the current Project Felt UI.
- [ ] MCP screenshot captures an authenticated, approved write and successful
      tool-result evidence, not just an AI claim. If no tool calls are available,
      change the lab result accordingly.
- [ ] Two students independently finish in 45 minutes or the timing is revised.
