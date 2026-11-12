# Pinned Showroom UI bundle

The Antora playbook uses `showroom-v2.0.3.zip` directly from this directory.
GitHub Pages no longer downloads a GitHub release asset during builds.

- Upstream: <https://github.com/rhpds/rhdp_showroom_theme>
- Release: <https://github.com/rhpds/rhdp_showroom_theme/releases/tag/v2.0.3>
- Asset: `ui-bundle.zip` from that release, stored unchanged as `showroom-v2.0.3.zip`
- License: MPL-2.0 (see `SHOWROOM-UI-LICENSE`)
- SHA-256: `268878dd4a37f1e73876620f68a40787c7c8984ae21c6dc882538c83de3a5270`

To upgrade, explicitly download a different tagged release and review it,
then commit its ZIP under a new versioned filename. Update the `url` in
`site.yml`, the SHA-256 checksum file and the verification step in
`.github/workflows/gh-pages.yml`. Check the ZIP with `unzip -t` before
committing. Do not replace the binary in place without updating the checksum.

This only removes the **UI bundle release download** from the Pages build;
the `npm install` step still needs its usual package registry access.
