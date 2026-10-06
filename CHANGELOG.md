# Changelog

## 1.0.0 — 2026-10-06

- First publishable release of `ryzen-stabilizator-service-units-installer`.
- Installs independent systemd controls for AMD Family 17h Package C6, AMD Family 17h Core C6, CPU boost, and kernel ASLR.
- Adds a live `ryzen-stabilizator-status.service` that reads actual MSR/sysfs/sysctl state.
- Uses `systemctl enable --now` to apply a disable-control immediately and at boot, and `systemctl disable --now` to restore the saved current-boot state.
- Adds APT repository validation and `msr-tools` installation for Proxmox/Debian hosts.
- Adds README synchronization and clipboard/bookmarklet helper generated from the single `paste-to-run.sh` source.
