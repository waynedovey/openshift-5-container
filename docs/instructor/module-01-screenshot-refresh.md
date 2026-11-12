# Module 1: completed student screenshot update

Three actual student screenshots were added to this PR under
`content/modules/ROOT/images/`. They are already referenced from
`content/modules/ROOT/pages/module-01-whats-new-in-ocp5.adoc`.

| Screenshot | Repository file | Placement |
|---|---|---|
| Successful Showroom Terminal login | `module01-student-login-success.png` | Mission 0, below `oc login` |
| Populated National Parks map | `module01-s01-map.png` | Mission 6, working park markers |
| OpenShift 5 Topology with three components | `module01-s02-topology.png` | Mission 6, application overview |

The login PNG has its password redacted. Never commit the unredacted
source screenshot. The S01 and S02 images are from the student
environment, resized to keep Showroom pages responsive.

## Reviewer checks

1. Mission 0 displays `Login successful` with no password visible.
2. Mission 6 displays the actual park map with clustered markers and the
   `National Parks (PY)` layer enabled.
3. Mission 6 displays the three application components: `parksmap`,
   `national-parks-app` and `mongodb-nationalparks`.
4. The three `image::` references match files committed in this branch.

No student upload or Git command is required. Screenshots ship in the
Showroom source. A live rendered Showroom check is still advisable.
