# Changelog

## 1.0.2 — 2026-10-06

- Uses GitHub's native copy-to-clipboard control on the generated `bash` installer code block.
- Removes the `copy.html` clipboard helper and GitHub Pages deployment workflow.
- Keeps `paste-to-run.sh` as the single source of truth; `tools/sync_readme.py` now only regenerates the README code block.

## 1.0.1 — 2026-10-06

- Simplifies the README introduction and removes the non-working README bookmarklet.
- Adds a real JavaScript clipboard button in `copy.html` that fetches `paste-to-run.sh` at click time.
- Uses a `bash` fenced block for shell syntax highlighting.
- Adds GitHub Pages deployment for the clipboard helper and keeps the README copy-button target synchronized automatically.

## 1.0.0 — 2026-10-06

- First publishable release of `ryzen-stabilizator-service-units-installer`.
- Installs independent systemd controls for AMD Family 17h Package C6, AMD Family 17h Core C6, CPU boost, and kernel ASLR.
- Adds a live `ryzen-stabilizator-status.service` that reads actual MSR/sysfs/sysctl state.
- Uses `systemctl enable --now` to apply a disable-control immediately and at boot, and `systemctl disable --now` to restore the saved current-boot state.
- Adds APT repository validation and `msr-tools` installation for Proxmox/Debian hosts.
- Adds README synchronization and clipboard helper generated from the single `paste-to-run.sh` source.
