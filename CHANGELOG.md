# Changelog

## 1.0.6

- `systemctl start ryzen-stabilizator-status` now prints one ready-to-run opposite action for each of the four disable-controls.
- Enabled/active disable-controls are shown with `systemctl disable --now ...`; inactive controls are shown with `systemctl enable --now ...`.
- Printed toggle commands omit the optional `.service` suffix.
- Updated the README status explanation while keeping the quick-start section concise.

## 1.0.5

- Removed the optional `.service` suffix from user-facing `systemctl` examples.
- Grouped all enable commands together and all disable commands together in the quick-command section.
- Added a one-line clarification that disabling a `*-disable` service restores/re-enables the corresponding feature.
