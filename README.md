# ryzen-stabilizator-service-units-installer

Paste-to-run POSIX-shell installer for Proxmox/Debian systems with AMD Family 17h CPUs, especially first-generation Ryzen systems affected by unexplained freezes or idle-related instability. It installs independent systemd controls for Package C6, Core C6, CPU boost, and kernel ASLR, with Package C6 disabled by default as the conservative stability workaround.

<!-- BEGIN COPY BUTTON -->
<a href="copy.html"><kbd>📋 Copy paste-to-run.sh</kbd></a>
<!-- END COPY BUTTON -->

## Paste-to-run

<!-- BEGIN GENERATED PASTE-TO-RUN -->

```bash
init_colors(){ if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then RED=$(printf '\033[31m'); GREEN=$(printf '\033[32m'); YELLOW=$(printf '\033[33m'); CYAN=$(printf '\033[36m'); BOLD=$(printf '\033[1m'); RESET=$(printf '\033[0m'); else RED=; GREEN=; YELLOW=; CYAN=; BOLD=; RESET=; fi; }; info(){ printf '%s[INFO]%s %s\n' "$CYAN" "$RESET" "$*"; printf '[INFO] %s\n' "$*" >>"${LOG_FILE:-/var/log/ryzen-stabilizator.log}" 2>/dev/null; return 0; }; pass(){ printf '%s[PASS]%s %s\n' "$GREEN" "$RESET" "$*"; printf '[PASS] %s\n' "$*" >>"${LOG_FILE:-/var/log/ryzen-stabilizator.log}" 2>/dev/null; return 0; }; warn(){ printf '%s[WARN]%s %s\n' "$YELLOW" "$RESET" "$*" >&2; printf '[WARN] %s\n' "$*" >>"${LOG_FILE:-/var/log/ryzen-stabilizator.log}" 2>/dev/null; return 0; }; fail(){ printf '%s[FAIL]%s %s\n' "$RED" "$RESET" "$*" >&2; printf '[FAIL] %s\n' "$*" >>"${LOG_FILE:-/var/log/ryzen-stabilizator.log}" 2>/dev/null; return 0; }; define_constants(){ SYSTEMD_DIR=/etc/systemd/system; LOG_FILE=/var/log/ryzen-stabilizator.log; APT_BACKUP_DIR=/var/backups/ryzen-stabilizator/apt; PACKAGE_C6_SERVICE=amd-family17h-package-c6-disable.service; CORE_C6_SERVICE=amd-family17h-core-c6-disable.service; BOOST_SERVICE=cpu-boost-disable.service; ASLR_SERVICE=kernel-aslr-disable.service; STATUS_SERVICE=ryzen-stabilizator-status.service; }; require_root(){ if [ "$(id -u)" -eq 0 ]; then pass "Running as root"; return 0; else fail "This installer must be run as root"; return 1; fi; }; setup_log(){ if touch "$LOG_FILE" 2>/dev/null && chmod 0644 "$LOG_FILE" 2>/dev/null; then pass "Logging to $LOG_FILE"; return 0; else fail "Cannot write log $LOG_FILE"; return 1; fi; }; require_msr_tools(){ if command -v rdmsr >/dev/null 2>&1 && command -v wrmsr >/dev/null 2>&1; then return 0; else fail "msr-tools is not installed"; return 1; fi; }; unit_state(){ us=$(systemctl is-enabled "$1" 2>/dev/null); [ -n "$us" ] || us=unknown; printf '%s' "$us"; }; log_unit_failure(){ info "Saving diagnostics for $1"; systemctl status "$1" --no-pager >>"$LOG_FILE" 2>&1; journalctl -u "$1" -n 100 --no-pager >>"$LOG_FILE" 2>&1; return 0; }; reload_systemd(){ info "Reloading systemd configuration"; if systemctl daemon-reload >>"$LOG_FILE" 2>&1; then pass "Reloaded systemd configuration"; return 0; else fail "Failed to reload systemd configuration; see $LOG_FILE"; return 1; fi; }; remove_unsigned_repos(){ info "Checking configured APT repositories with apt-secure"; mkdir -p "$APT_BACKUP_DIR" || { fail "Could not create $APT_BACKUP_DIR"; return 1; }; for rur_old in /etc/apt/sources.list.d/*.before-remove-unsigned; do [ -f "$rur_old" ] || continue; mv -f "$rur_old" "$APT_BACKUP_DIR/$(basename "$rur_old")" 2>/dev/null || :; done; rur_tmp=$(mktemp -d) || { fail "Could not create temporary directory for repository checks"; return 1; }; rur_removed=0; for rur_file in /etc/apt/sources.list /etc/apt/sources.list.d/*.list; do [ -f "$rur_file" ] || continue; cp "$rur_file" "$rur_tmp/source.list" || continue; rur_line=0; while IFS= read -r rur_entry || [ -n "$rur_entry" ]; do rur_line=$((rur_line+1)); case "$rur_entry" in ''|\#*) continue;; deb\ *|deb-src\ *) :;; *) continue;; esac; printf '%s\n' "$rur_entry" >"$rur_tmp/test.list"; rm -rf "$rur_tmp/lists"; mkdir -p "$rur_tmp/lists/partial"; rur_out=$(apt-get -o Dir::Etc::sourcelist="$rur_tmp/test.list" -o Dir::Etc::sourceparts=- -o Dir::State::lists="$rur_tmp/lists" -o Debug::NoLocking=1 -o Acquire::Languages=none -o Acquire::AllowInsecureRepositories=false -o Acquire::AllowDowngradeToInsecureRepositories=false update -qq 2>&1); rur_rc=$?; if printf '%s\n' "$rur_out" | grep -Eqi '401 Unauthorized|NO_PUBKEY|EXPKEYSIG|BADSIG|invalid signature|signatures? (couldn.t|could not) be verified|signatures? were invalid|At least one invalid signature|Clearsigned file .* isn.t valid|Signed file .* isn.t valid|repository .* (is|was) not signed|does not have a Release file'; then rur_backup="$APT_BACKUP_DIR/$(basename "$rur_file").before-remove-unsigned"; [ -e "$rur_backup" ] || cp -p "$rur_file" "$rur_backup"; awk -v n="$rur_line" 'NR==n{$0="# disabled by remove_unsigned_repos: "$0}{print}' "$rur_file" >"$rur_tmp/rewrite" && cat "$rur_tmp/rewrite" >"$rur_file"; warn "Disabled repository failing apt signature/authentication verification: $rur_entry"; printf '[WARN] apt-secure output for %s line %s:\n%s\n' "$rur_file" "$rur_line" "$rur_out" >>"$LOG_FILE"; rur_removed=$((rur_removed+1)); elif [ "$rur_rc" -eq 0 ]; then pass "Repository signature OK: $rur_entry"; else warn "Repository check inconclusive; leaving enabled: $rur_entry"; printf '[WARN] inconclusive repository check for %s line %s:\n%s\n' "$rur_file" "$rur_line" "$rur_out" >>"$LOG_FILE"; fi; done <"$rur_tmp/source.list"; done; for rur_file in /etc/apt/sources.list.d/*.sources; do [ -f "$rur_file" ] || continue; awk 'BEGIN{s=1;a=0;d=0} /^[[:space:]]*$/{if(a&&!d)print s ":" NR-1;s=NR+1;a=0;d=0;next} /^[[:space:]]*(Types|URIs):/{a=1} /^[[:space:]]*Enabled:[[:space:]]*[Nn][Oo]([[:space:]]|$)/{d=1} END{if(a&&!d)print s ":" NR}' "$rur_file" >"$rur_tmp/ranges"; while IFS=: read -r rur_start rur_end; do [ -n "$rur_start" ] || continue; sed -n "${rur_start},${rur_end}p" "$rur_file" >"$rur_tmp/test.sources"; rm -rf "$rur_tmp/lists"; mkdir -p "$rur_tmp/lists/partial"; rur_out=$(apt-get -o Dir::Etc::sourcelist="$rur_tmp/test.sources" -o Dir::Etc::sourceparts=- -o Dir::State::lists="$rur_tmp/lists" -o Debug::NoLocking=1 -o Acquire::Languages=none -o Acquire::AllowInsecureRepositories=false -o Acquire::AllowDowngradeToInsecureRepositories=false update -qq 2>&1); rur_rc=$?; rur_name=$(awk '/^[[:space:]]*URIs:/{sub(/^[[:space:]]*URIs:[[:space:]]*/,"");print;exit}' "$rur_tmp/test.sources"); [ -n "$rur_name" ] || rur_name="$rur_file:$rur_start-$rur_end"; if printf '%s\n' "$rur_out" | grep -Eqi '401 Unauthorized|NO_PUBKEY|EXPKEYSIG|BADSIG|invalid signature|signatures? (couldn.t|could not) be verified|signatures? were invalid|At least one invalid signature|Clearsigned file .* isn.t valid|Signed file .* isn.t valid|repository .* (is|was) not signed|does not have a Release file'; then rur_backup="$APT_BACKUP_DIR/$(basename "$rur_file").before-remove-unsigned"; [ -e "$rur_backup" ] || cp -p "$rur_file" "$rur_backup"; awk -v s="$rur_start" -v e="$rur_end" 'NR>=s&&NR<=e&&$0!~/^[[:space:]]*#/&&$0!~/^[[:space:]]*$/{ $0="# disabled by remove_unsigned_repos: "$0 }{print}' "$rur_file" >"$rur_tmp/rewrite" && cat "$rur_tmp/rewrite" >"$rur_file"; warn "Disabled repository stanza failing apt signature/authentication verification: $rur_name"; printf '[WARN] apt-secure output for %s lines %s-%s:\n%s\n' "$rur_file" "$rur_start" "$rur_end" "$rur_out" >>"$LOG_FILE"; rur_removed=$((rur_removed+1)); elif [ "$rur_rc" -eq 0 ]; then pass "Repository signature OK: $rur_name"; else warn "Repository check inconclusive; leaving enabled: $rur_name"; printf '[WARN] inconclusive repository check for %s lines %s-%s:\n%s\n' "$rur_file" "$rur_start" "$rur_end" "$rur_out" >>"$LOG_FILE"; fi; done <"$rur_tmp/ranges"; done; rm -rf "$rur_tmp"; if [ "$rur_removed" -eq 0 ]; then pass "No repositories failing signature/authentication verification found"; else warn "Disabled $rur_removed repository entry/stanza(s); backups stored in $APT_BACKUP_DIR"; fi; return 0; }; install_dependencies(){ remove_unsigned_repos; if dpkg-query -W -f='${Status}' msr-tools 2>/dev/null | grep -q 'ok installed'; then pass "msr-tools already installed"; else info "Installing msr-tools"; if apt-get update -qq >>"$LOG_FILE" 2>&1 && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq -o=Dpkg::Use-Pty=0 msr-tools >>"$LOG_FILE" 2>&1; then pass "Installed msr-tools"; else fail "Failed to install msr-tools; see $LOG_FILE"; return 1; fi; fi; }; cleanup_legacy_units(){ info "Removing legacy Ryzen Stabilizator unit definitions"; for u in ryzen-psic-workaround.service ryzen-disable-core-c6.service ryzen-disable-boost.service ryzen-disable-aslr.service ryzen-stabilizator-boot.service ryzen-status.service; do if systemctl cat "$u" >/dev/null 2>&1; then systemctl disable "$u" >/dev/null 2>&1 || :; systemctl stop "$u" >/dev/null 2>&1 || :; fi; rm -f "$SYSTEMD_DIR/$u"; done; pass "Legacy unit definitions cleaned up"; }; create_package_c6_service(){ if printf '%s\n' '[Unit]' 'Description=AMD Family 17h - Disable Package C6' 'After=systemd-modules-load.service' 'Before=pve-guests.service' '' '[Service]' 'Type=oneshot' 'RemainAfterExit=yes' 'SyslogIdentifier=amd-family17h-package-c6-disable' 'ExecCondition=/bin/grep -qm1 AuthenticAMD /proc/cpuinfo' 'ExecCondition=/bin/grep -Eqm1 "cpu family[[:space:]]*:[[:space:]]*23" /proc/cpuinfo' 'ExecStart=/bin/sh -c "find_tty(){ tty=; for p in /proc/[0-9]*; do case \"$$(readlink \"$$p/exe\" 2>/dev/null)\" in */systemctl) c=$$(tr \"\\0\" \" \" <\"$$p/cmdline\" 2>/dev/null); case \"$$c\" in *amd-family17h-package-c6-disable*) t=$$(readlink \"$$p/fd/1\" 2>/dev/null); case \"$$t\" in /dev/pts/*|/dev/tty*) tty=$$t; break;; esac;; esac;; esac; done; }; emit(){ printf \"%%s\\n\" \"$$1\"; [ -n \"$$tty\" ] && [ -w \"$$tty\" ] && printf \"%%b\\n\" \"$${2:-$$1}\" >\"$$tty\"; }; find_tty; Y=$$(printf \"\\033[1;33m\"); R=$$(printf \"\\033[1;31m\"); Z=$$(printf \"\\033[0m\"); d=/run/amd-family17h-package-c6-disable; rm -rf \"$$d\"; mkdir -p \"$$d\" || exit 1; modprobe msr || exit 1; found=0; for f in /dev/cpu/[0-9]*/msr; do [ -e \"$$f\" ] || continue; c=$$(basename $$(dirname \"$$f\")); v=$$(rdmsr -d -p \"$$c\" 0xC0010292) || exit 1; m=$$((v & 4294967296)); printf \"%%s\\n\" \"$$m\" >\"$$d/$$c\" || exit 1; found=1; done; [ \"$$found\" -eq 1 ] || { emit \"Package C6 : ERROR - No CPU MSR devices were found.\" \"Package C6 : $${R}ERROR$${Z} - No CPU MSR devices were found.\"; exit 1; }; for f in /dev/cpu/[0-9]*/msr; do [ -e \"$$f\" ] || continue; c=$$(basename $$(dirname \"$$f\")); v=$$(rdmsr -d -p \"$$c\" 0xC0010292) || exit 1; n=$$((v & ~4294967296)); h=$$(printf \"%%016x\" \"$$n\"); wrmsr -p \"$$c\" 0xC0010292 \"0x$$h\" || exit 1; done; v=$$(rdmsr -a -f 32:32 -u 0xC0010292 2>/dev/null) || exit 1; if printf \"%%s\\n\" \"$$v\" | awk '\''$$NF!=0{bad=1}END{exit bad}'\''; then emit \"Package C6 : DISABLED - Package-wide deep idle state; package-level C6 entry is disabled.\" \"Package C6 : $${Y}DISABLED$${Z} - Package-wide deep idle state; package-level C6 entry is disabled.\"; else emit \"Package C6 : ERROR - MSR readback did not confirm Package C6 disabled.\" \"Package C6 : $${R}ERROR$${Z} - MSR readback did not confirm Package C6 disabled.\"; exit 1; fi"' 'ExecStop=/bin/sh -c "find_tty(){ tty=; for p in /proc/[0-9]*; do case \"$$(readlink \"$$p/exe\" 2>/dev/null)\" in */systemctl) c=$$(tr \"\\0\" \" \" <\"$$p/cmdline\" 2>/dev/null); case \"$$c\" in *amd-family17h-package-c6-disable*) t=$$(readlink \"$$p/fd/1\" 2>/dev/null); case \"$$t\" in /dev/pts/*|/dev/tty*) tty=$$t; break;; esac;; esac;; esac; done; }; emit(){ printf \"%%s\\n\" \"$$1\"; [ -n \"$$tty\" ] && [ -w \"$$tty\" ] && printf \"%%b\\n\" \"$${2:-$$1}\" >\"$$tty\"; }; find_tty; G=$$(printf \"\\033[1;32m\"); Y=$$(printf \"\\033[1;33m\"); R=$$(printf \"\\033[1;31m\"); Z=$$(printf \"\\033[0m\"); d=/run/amd-family17h-package-c6-disable; [ -d \"$$d\" ] || { emit \"Package C6 : ERROR - No saved pre-disable MSR state is available.\" \"Package C6 : $${R}ERROR$${Z} - No saved pre-disable MSR state is available.\"; exit 1; }; modprobe msr || exit 1; for f in /dev/cpu/[0-9]*/msr; do [ -e \"$$f\" ] || continue; c=$$(basename $$(dirname \"$$f\")); [ -r \"$$d/$$c\" ] || continue; m=$$(cat \"$$d/$$c\") || exit 1; v=$$(rdmsr -d -p \"$$c\" 0xC0010292) || exit 1; n=$$(((v & ~4294967296) | m)); h=$$(printf \"%%016x\" \"$$n\"); wrmsr -p \"$$c\" 0xC0010292 \"0x$$h\" || exit 1; done; rm -rf \"$$d\"; v=$$(rdmsr -a -f 32:32 -u 0xC0010292 2>/dev/null) || exit 1; if printf \"%%s\\n\" \"$$v\" | awk '\''$$NF!=0{bad=1}END{exit bad}'\''; then emit \"Package C6 : DISABLED - Original current-boot Package C6 state restored.\" \"Package C6 : $${Y}DISABLED$${Z} - Original current-boot Package C6 state restored.\"; else emit \"Package C6 : ENABLED - Original current-boot Package C6 state restored.\" \"Package C6 : $${G}ENABLED$${Z} - Original current-boot Package C6 state restored.\"; fi"' 'StandardOutput=journal' 'StandardError=journal' '' '[Install]' 'WantedBy=multi-user.target' >"$SYSTEMD_DIR/$PACKAGE_C6_SERVICE"; then pass "Created $PACKAGE_C6_SERVICE"; return 0; else fail "Failed to create $PACKAGE_C6_SERVICE"; return 1; fi; }; create_core_c6_service(){ if printf '%s\n' '[Unit]' 'Description=AMD Family 17h - Disable Core C6' 'After=systemd-modules-load.service' 'Before=pve-guests.service' '' '[Service]' 'Type=oneshot' 'RemainAfterExit=yes' 'SyslogIdentifier=amd-family17h-core-c6-disable' 'ExecCondition=/bin/grep -qm1 AuthenticAMD /proc/cpuinfo' 'ExecCondition=/bin/grep -Eqm1 "cpu family[[:space:]]*:[[:space:]]*23" /proc/cpuinfo' 'ExecStart=/bin/sh -c "find_tty(){ tty=; for p in /proc/[0-9]*; do case \"$$(readlink \"$$p/exe\" 2>/dev/null)\" in */systemctl) c=$$(tr \"\\0\" \" \" <\"$$p/cmdline\" 2>/dev/null); case \"$$c\" in *amd-family17h-core-c6-disable*) t=$$(readlink \"$$p/fd/1\" 2>/dev/null); case \"$$t\" in /dev/pts/*|/dev/tty*) tty=$$t; break;; esac;; esac;; esac; done; }; emit(){ printf \"%%s\\n\" \"$$1\"; [ -n \"$$tty\" ] && [ -w \"$$tty\" ] && printf \"%%b\\n\" \"$${2:-$$1}\" >\"$$tty\"; }; find_tty; Y=$$(printf \"\\033[1;33m\"); R=$$(printf \"\\033[1;31m\"); Z=$$(printf \"\\033[0m\"); d=/run/amd-family17h-core-c6-disable; rm -rf \"$$d\"; mkdir -p \"$$d\" || exit 1; modprobe msr || exit 1; found=0; for f in /dev/cpu/[0-9]*/msr; do [ -e \"$$f\" ] || continue; c=$$(basename $$(dirname \"$$f\")); v=$$(rdmsr -d -p \"$$c\" 0xC0010296) || exit 1; m=$$((v & 4210752)); printf \"%%s\\n\" \"$$m\" >\"$$d/$$c\" || exit 1; found=1; done; [ \"$$found\" -eq 1 ] || { emit \"Core C6 : ERROR - No CPU MSR devices were found.\" \"Core C6 : $${R}ERROR$${Z} - No CPU MSR devices were found.\"; exit 1; }; for f in /dev/cpu/[0-9]*/msr; do [ -e \"$$f\" ] || continue; c=$$(basename $$(dirname \"$$f\")); v=$$(rdmsr -d -p \"$$c\" 0xC0010296) || exit 1; n=$$((v & ~4210752)); h=$$(printf \"%%016x\" \"$$n\"); wrmsr -p \"$$c\" 0xC0010296 \"0x$$h\" || exit 1; done; v=$$( { rdmsr -a -f 22:22 -u 0xC0010296; rdmsr -a -f 14:14 -u 0xC0010296; rdmsr -a -f 6:6 -u 0xC0010296; } 2>/dev/null) || exit 1; if printf \"%%s\\n\" \"$$v\" | awk '\''$$NF!=0{bad=1}END{exit bad}'\''; then emit \"Core C6 : DISABLED - Per-core deep idle state; CC6 entry is disabled.\" \"Core C6 : $${Y}DISABLED$${Z} - Per-core deep idle state; CC6 entry is disabled.\"; else emit \"Core C6 : ERROR - MSR readback did not confirm Core C6 disabled.\" \"Core C6 : $${R}ERROR$${Z} - MSR readback did not confirm Core C6 disabled.\"; exit 1; fi"' 'ExecStop=/bin/sh -c "find_tty(){ tty=; for p in /proc/[0-9]*; do case \"$$(readlink \"$$p/exe\" 2>/dev/null)\" in */systemctl) c=$$(tr \"\\0\" \" \" <\"$$p/cmdline\" 2>/dev/null); case \"$$c\" in *amd-family17h-core-c6-disable*) t=$$(readlink \"$$p/fd/1\" 2>/dev/null); case \"$$t\" in /dev/pts/*|/dev/tty*) tty=$$t; break;; esac;; esac;; esac; done; }; emit(){ printf \"%%s\\n\" \"$$1\"; [ -n \"$$tty\" ] && [ -w \"$$tty\" ] && printf \"%%b\\n\" \"$${2:-$$1}\" >\"$$tty\"; }; find_tty; G=$$(printf \"\\033[1;32m\"); Y=$$(printf \"\\033[1;33m\"); R=$$(printf \"\\033[1;31m\"); Z=$$(printf \"\\033[0m\"); d=/run/amd-family17h-core-c6-disable; [ -d \"$$d\" ] || { emit \"Core C6 : ERROR - No saved pre-disable MSR state is available.\" \"Core C6 : $${R}ERROR$${Z} - No saved pre-disable MSR state is available.\"; exit 1; }; modprobe msr || exit 1; for f in /dev/cpu/[0-9]*/msr; do [ -e \"$$f\" ] || continue; c=$$(basename $$(dirname \"$$f\")); [ -r \"$$d/$$c\" ] || continue; m=$$(cat \"$$d/$$c\") || exit 1; v=$$(rdmsr -d -p \"$$c\" 0xC0010296) || exit 1; n=$$(((v & ~4210752) | m)); h=$$(printf \"%%016x\" \"$$n\"); wrmsr -p \"$$c\" 0xC0010296 \"0x$$h\" || exit 1; done; rm -rf \"$$d\"; v=$$( { rdmsr -a -f 22:22 -u 0xC0010296; rdmsr -a -f 14:14 -u 0xC0010296; rdmsr -a -f 6:6 -u 0xC0010296; } 2>/dev/null) || exit 1; if printf \"%%s\\n\" \"$$v\" | awk '\''$$NF!=0{bad=1}END{exit bad}'\''; then emit \"Core C6 : DISABLED - Original current-boot Core C6 state restored.\" \"Core C6 : $${Y}DISABLED$${Z} - Original current-boot Core C6 state restored.\"; else emit \"Core C6 : ENABLED - Original current-boot Core C6 state restored.\" \"Core C6 : $${G}ENABLED$${Z} - Original current-boot Core C6 state restored.\"; fi"' 'StandardOutput=journal' 'StandardError=journal' '' '[Install]' 'WantedBy=multi-user.target' >"$SYSTEMD_DIR/$CORE_C6_SERVICE"; then pass "Created $CORE_C6_SERVICE"; return 0; else fail "Failed to create $CORE_C6_SERVICE"; return 1; fi; }; create_boost_service(){ if printf '%s\n' '[Unit]' 'Description=Disable CPU Boost' 'Before=pve-guests.service' '' '[Service]' 'Type=oneshot' 'RemainAfterExit=yes' 'SyslogIdentifier=cpu-boost-disable' 'ExecStart=/bin/sh -c "find_tty(){ tty=; for p in /proc/[0-9]*; do case \"$$(readlink \"$$p/exe\" 2>/dev/null)\" in */systemctl) c=$$(tr \"\\0\" \" \" <\"$$p/cmdline\" 2>/dev/null); case \"$$c\" in *cpu-boost-disable*) t=$$(readlink \"$$p/fd/1\" 2>/dev/null); case \"$$t\" in /dev/pts/*|/dev/tty*) tty=$$t; break;; esac;; esac;; esac; done; }; emit(){ printf \"%%s\\n\" \"$$1\"; [ -n \"$$tty\" ] && [ -w \"$$tty\" ] && printf \"%%b\\n\" \"$${2:-$$1}\" >\"$$tty\"; }; find_tty; Y=$$(printf \"\\033[1;33m\"); R=$$(printf \"\\033[1;31m\"); Z=$$(printf \"\\033[0m\"); p=/sys/devices/system/cpu/cpufreq/boost; [ -r \"$$p\" ] && [ -w \"$$p\" ] || { emit \"CPU Boost : ERROR - boost control is unavailable through sysfs.\" \"CPU Boost : $${R}ERROR$${Z} - boost control is unavailable through sysfs.\"; exit 1; }; d=/run/cpu-boost-disable; rm -rf \"$$d\"; mkdir -p \"$$d\" || exit 1; cat \"$$p\" >\"$$d/original\" || exit 1; printf \"0\\n\" >\"$$p\" || exit 1; if [ \"$$(cat \"$$p\")\" = 0 ]; then emit \"CPU Boost : DISABLED - CPU frequency boost above the normal base operating range is disabled.\" \"CPU Boost : $${Y}DISABLED$${Z} - CPU frequency boost above the normal base operating range is disabled.\"; else emit \"CPU Boost : ERROR - sysfs readback did not confirm boost disabled.\" \"CPU Boost : $${R}ERROR$${Z} - sysfs readback did not confirm boost disabled.\"; exit 1; fi"' 'ExecStop=/bin/sh -c "find_tty(){ tty=; for p in /proc/[0-9]*; do case \"$$(readlink \"$$p/exe\" 2>/dev/null)\" in */systemctl) c=$$(tr \"\\0\" \" \" <\"$$p/cmdline\" 2>/dev/null); case \"$$c\" in *cpu-boost-disable*) t=$$(readlink \"$$p/fd/1\" 2>/dev/null); case \"$$t\" in /dev/pts/*|/dev/tty*) tty=$$t; break;; esac;; esac;; esac; done; }; emit(){ printf \"%%s\\n\" \"$$1\"; [ -n \"$$tty\" ] && [ -w \"$$tty\" ] && printf \"%%b\\n\" \"$${2:-$$1}\" >\"$$tty\"; }; find_tty; G=$$(printf \"\\033[1;32m\"); Y=$$(printf \"\\033[1;33m\"); R=$$(printf \"\\033[1;31m\"); Z=$$(printf \"\\033[0m\"); p=/sys/devices/system/cpu/cpufreq/boost; d=/run/cpu-boost-disable; [ -r \"$$d/original\" ] || { emit \"CPU Boost : ERROR - No saved pre-disable state is available.\" \"CPU Boost : $${R}ERROR$${Z} - No saved pre-disable state is available.\"; exit 1; }; v=$$(cat \"$$d/original\") || exit 1; printf \"%%s\\n\" \"$$v\" >\"$$p\" || exit 1; rm -rf \"$$d\"; v=$$(cat \"$$p\"); if [ \"$$v\" = 0 ]; then emit \"CPU Boost : DISABLED - Original current-boot boost state restored.\" \"CPU Boost : $${Y}DISABLED$${Z} - Original current-boot boost state restored.\"; else emit \"CPU Boost : ENABLED - Original current-boot boost state restored.\" \"CPU Boost : $${G}ENABLED$${Z} - Original current-boot boost state restored.\"; fi"' 'StandardOutput=journal' 'StandardError=journal' '' '[Install]' 'WantedBy=multi-user.target' >"$SYSTEMD_DIR/$BOOST_SERVICE"; then pass "Created $BOOST_SERVICE"; return 0; else fail "Failed to create $BOOST_SERVICE"; return 1; fi; }; create_aslr_service(){ if printf '%s\n' '[Unit]' 'Description=Disable Kernel ASLR' 'Before=pve-guests.service' '' '[Service]' 'Type=oneshot' 'RemainAfterExit=yes' 'SyslogIdentifier=kernel-aslr-disable' 'ExecStart=/bin/sh -c "find_tty(){ tty=; for p in /proc/[0-9]*; do case \"$$(readlink \"$$p/exe\" 2>/dev/null)\" in */systemctl) c=$$(tr \"\\0\" \" \" <\"$$p/cmdline\" 2>/dev/null); case \"$$c\" in *kernel-aslr-disable*) t=$$(readlink \"$$p/fd/1\" 2>/dev/null); case \"$$t\" in /dev/pts/*|/dev/tty*) tty=$$t; break;; esac;; esac;; esac; done; }; emit(){ printf \"%%s\\n\" \"$$1\"; [ -n \"$$tty\" ] && [ -w \"$$tty\" ] && printf \"%%b\\n\" \"$${2:-$$1}\" >\"$$tty\"; }; find_tty; Y=$$(printf \"\\033[1;33m\"); R=$$(printf \"\\033[1;31m\"); Z=$$(printf \"\\033[0m\"); p=/proc/sys/kernel/randomize_va_space; [ -r \"$$p\" ] && [ -w \"$$p\" ] || { emit \"ASLR : ERROR - randomize_va_space is unavailable or not writable.\" \"ASLR : $${R}ERROR$${Z} - randomize_va_space is unavailable or not writable.\"; exit 1; }; d=/run/kernel-aslr-disable; rm -rf \"$$d\"; mkdir -p \"$$d\" || exit 1; cat \"$$p\" >\"$$d/original\" || exit 1; printf \"0\\n\" >\"$$p\" || exit 1; if [ \"$$(cat \"$$p\")\" = 0 ]; then emit \"ASLR : DISABLED - Address-space randomization security feature is disabled. (randomize_va_space=0)\" \"ASLR : $${Y}DISABLED$${Z} - Address-space randomization security feature is disabled. (randomize_va_space=0)\"; else emit \"ASLR : ERROR - sysctl readback did not confirm ASLR disabled.\" \"ASLR : $${R}ERROR$${Z} - sysctl readback did not confirm ASLR disabled.\"; exit 1; fi"' 'ExecStop=/bin/sh -c "find_tty(){ tty=; for p in /proc/[0-9]*; do case \"$$(readlink \"$$p/exe\" 2>/dev/null)\" in */systemctl) c=$$(tr \"\\0\" \" \" <\"$$p/cmdline\" 2>/dev/null); case \"$$c\" in *kernel-aslr-disable*) t=$$(readlink \"$$p/fd/1\" 2>/dev/null); case \"$$t\" in /dev/pts/*|/dev/tty*) tty=$$t; break;; esac;; esac;; esac; done; }; emit(){ printf \"%%s\\n\" \"$$1\"; [ -n \"$$tty\" ] && [ -w \"$$tty\" ] && printf \"%%b\\n\" \"$${2:-$$1}\" >\"$$tty\"; }; find_tty; G=$$(printf \"\\033[1;32m\"); Y=$$(printf \"\\033[1;33m\"); R=$$(printf \"\\033[1;31m\"); Z=$$(printf \"\\033[0m\"); p=/proc/sys/kernel/randomize_va_space; d=/run/kernel-aslr-disable; [ -r \"$$d/original\" ] || { emit \"ASLR : ERROR - No saved pre-disable state is available.\" \"ASLR : $${R}ERROR$${Z} - No saved pre-disable state is available.\"; exit 1; }; v=$$(cat \"$$d/original\") || exit 1; printf \"%%s\\n\" \"$$v\" >\"$$p\" || exit 1; rm -rf \"$$d\"; v=$$(cat \"$$p\"); if [ \"$$v\" = 0 ]; then emit \"ASLR : DISABLED - Original current-boot ASLR state restored. (randomize_va_space=$$v)\" \"ASLR : $${Y}DISABLED$${Z} - Original current-boot ASLR state restored. (randomize_va_space=$$v)\"; else emit \"ASLR : ENABLED - Original current-boot ASLR state restored. (randomize_va_space=$$v)\" \"ASLR : $${G}ENABLED$${Z} - Original current-boot ASLR state restored. (randomize_va_space=$$v)\"; fi"' 'StandardOutput=journal' 'StandardError=journal' '' '[Install]' 'WantedBy=multi-user.target' >"$SYSTEMD_DIR/$ASLR_SERVICE"; then pass "Created $ASLR_SERVICE"; return 0; else fail "Failed to create $ASLR_SERVICE"; return 1; fi; }; create_status_service(){ if printf '%s\n' '[Unit]' 'Description=Ryzen Stabilizator - Live Status' 'After=systemd-modules-load.service' '' '[Service]' 'Type=oneshot' 'SyslogIdentifier=ryzen-stabilizator-status' 'ExecStart=/bin/sh -c "find_tty(){ tty=; i=0; while [ \"$$i\" -lt 10 ] && [ -z \"$$tty\" ]; do for p in /proc/[0-9]*; do case \"$$(readlink \"$$p/exe\" 2>/dev/null)\" in */systemctl) c=$$(tr \"\\0\" \" \" <\"$$p/cmdline\" 2>/dev/null); case \"$$c\" in *ryzen-stabilizator-status*) t=$$(readlink \"$$p/fd/1\" 2>/dev/null); case \"$$t\" in /dev/pts/*|/dev/tty*) tty=$$t; break;; esac;; esac;; esac; done; i=$$((i+1)); [ -n \"$$tty\" ] || sleep 0.05; done; }; emit(){ printf \"%%s\\n\" \"$$1\"; [ -n \"$$tty\" ] && [ -w \"$$tty\" ] && printf \"%%b\\n\" \"$${2:-$$1}\" >\"$$tty\"; }; line(){ label=$$1; state=$$2; desc=$$3; svc=$$4; extra=$$5; en=$$(systemctl is-enabled \"$$svc\" 2>/dev/null); [ -n \"$$en\" ] || en=unknown; ac=$$(systemctl is-active \"$$svc\" 2>/dev/null); [ -n \"$$ac\" ] || ac=unknown; mismatch=; if [ \"$$state\" != DISABLED ] && { [ \"$$en\" = enabled ] || [ \"$$ac\" = active ]; }; then mismatch=\" [SERVICE MISMATCH: $$en/$$ac]\"; fi; case \"$$state\" in ENABLED) col=$$G;; DISABLED) col=$$Y;; *) col=$$R;; esac; plain=$$(printf \"%%-11s : %%-8s - %%s%%s%%s\" \"$$label\" \"$$state\" \"$$desc\" \"$$extra\" \"$$mismatch\"); colored=$$(printf \"%%-11s : %%b%%-8s%%b - %%s%%s%%b%%s%%b\" \"$$label\" \"$$col\" \"$$state\" \"$$Z\" \"$$desc\" \"$$extra\" \"$$R\" \"$$mismatch\" \"$$Z\"); emit \"$$plain\" \"$$colored\"; }; find_tty; G=$$(printf \"\\033[1;32m\"); Y=$$(printf \"\\033[1;33m\"); R=$$(printf \"\\033[1;31m\"); C=$$(printf \"\\033[1;36m\"); B=$$(printf \"\\033[1m\"); Z=$$(printf \"\\033[0m\"); emit \"=== Ryzen Stabilizator Status ===\" \"$${B}$${C}=== Ryzen Stabilizator Status ===$${Z}\"; if grep -qm1 AuthenticAMD /proc/cpuinfo && grep -Eqm1 \"cpu family[[:space:]]*:[[:space:]]*23\" /proc/cpuinfo; then modprobe msr >/dev/null 2>&1; if command -v rdmsr >/dev/null 2>&1 && v=$$(rdmsr -a -f 32:32 -u 0xC0010292 2>/dev/null); then if printf \"%%s\\n\" \"$$v\" | awk '\''$$NF!=0{bad=1}END{exit bad}'\''; then s=DISABLED; else s=ENABLED; fi; line \"Package C6\" \"$$s\" \"Package-wide deep idle state; disabling it prevents package-level C6 entry.\" amd-family17h-package-c6-disable.service \"\"; else line \"Package C6\" UNKNOWN \"Package-wide deep idle state; unable to read AMD MSR 0xC0010292.\" amd-family17h-package-c6-disable.service \"\"; fi; if command -v rdmsr >/dev/null 2>&1 && v=$$( { rdmsr -a -f 22:22 -u 0xC0010296; rdmsr -a -f 14:14 -u 0xC0010296; rdmsr -a -f 6:6 -u 0xC0010296; } 2>/dev/null); then if printf \"%%s\\n\" \"$$v\" | awk '\''$$NF!=0{bad=1}END{exit bad}'\''; then s=DISABLED; else s=ENABLED; fi; line \"Core C6\" \"$$s\" \"Per-core deep idle state; individual CPU cores may enter the CC6 low-power state.\" amd-family17h-core-c6-disable.service \"\"; else line \"Core C6\" UNKNOWN \"Per-core deep idle state; unable to read AMD MSR 0xC0010296.\" amd-family17h-core-c6-disable.service \"\"; fi; else line \"Package C6\" UNSUPPORTED \"MSR control is restricted to AMD Family 17h CPUs.\" amd-family17h-package-c6-disable.service \"\"; line \"Core C6\" UNSUPPORTED \"MSR control is restricted to AMD Family 17h CPUs.\" amd-family17h-core-c6-disable.service \"\"; fi; p=/sys/devices/system/cpu/cpufreq/boost; if [ -r \"$$p\" ]; then v=$$(cat \"$$p\"); if [ \"$$v\" = 0 ]; then s=DISABLED; else s=ENABLED; fi; line \"CPU Boost\" \"$$s\" \"Allows CPU frequency to rise above its normal base operating frequency.\" cpu-boost-disable.service \"\"; else line \"CPU Boost\" UNKNOWN \"CPU boost control is unavailable through sysfs.\" cpu-boost-disable.service \"\"; fi; p=/proc/sys/kernel/randomize_va_space; if [ -r \"$$p\" ]; then v=$$(cat \"$$p\"); if [ \"$$v\" = 0 ]; then s=DISABLED; else s=ENABLED; fi; line ASLR \"$$s\" \"Address-space randomization security feature.\" kernel-aslr-disable.service \" (randomize_va_space=$$v)\"; else line ASLR UNKNOWN \"Address-space randomization state is unavailable.\" kernel-aslr-disable.service \"\"; fi; emit \"\"; emit \"Run again: systemctl start ryzen-stabilizator-status\" \"$${C}Run again:$${Z} systemctl start ryzen-stabilizator-status\""' 'StandardOutput=journal' 'StandardError=journal' >"$SYSTEMD_DIR/$STATUS_SERVICE"; then pass "Created $STATUS_SERVICE"; return 0; else fail "Failed to create $STATUS_SERVICE"; return 1; fi; }; create_systemd_service_unit_files(){ info "Creating setting-control systemd units"; SERVICE_ERRORS=0; create_package_c6_service || SERVICE_ERRORS=1; create_core_c6_service || SERVICE_ERRORS=1; create_boost_service || SERVICE_ERRORS=1; create_aslr_service || SERVICE_ERRORS=1; create_status_service || SERVICE_ERRORS=1; if [ "$SERVICE_ERRORS" -eq 0 ]; then pass "Created all setting-control service units"; return 0; else fail "One or more service units could not be created"; return 1; fi; }; verify_systemd_service_unit_files(){ info "Verifying systemd service units"; if systemd-analyze verify "$SYSTEMD_DIR/$PACKAGE_C6_SERVICE" "$SYSTEMD_DIR/$CORE_C6_SERVICE" "$SYSTEMD_DIR/$BOOST_SERVICE" "$SYSTEMD_DIR/$ASLR_SERVICE" "$SYSTEMD_DIR/$STATUS_SERVICE" >>"$LOG_FILE" 2>&1; then pass "All service units passed verification"; return 0; else fail "One or more service units failed verification; see $LOG_FILE"; return 1; fi; }; print_install_status(){ printf '\n%s%sInstalled setting controls%s\n' "$BOLD" "$GREEN" "$RESET"; printf '  %-48s %s\n' "$PACKAGE_C6_SERVICE" "$(unit_state "$PACKAGE_C6_SERVICE")"; printf '  %-48s %s\n' "$CORE_C6_SERVICE" "$(unit_state "$CORE_C6_SERVICE")"; printf '  %-48s %s\n' "$BOOST_SERVICE" "$(unit_state "$BOOST_SERVICE")"; printf '  %-48s %s\n' "$ASLR_SERVICE" "$(unit_state "$ASLR_SERVICE")"; printf '  %-48s %s\n\n' "$STATUS_SERVICE" 'oneshot status'; info "Enable a disable-control immediately and at boot with: systemctl enable --now <service>"; info "Restore it immediately and remove boot persistence with: systemctl disable --now <service>"; info "Status command: systemctl start ryzen-stabilizator-status"; info "Full diagnostics: $LOG_FILE"; }; install_ryzen_stabilizator(){ init_colors; define_constants; require_root || return 1; setup_log || return 1; info "Installing Ryzen/CPU setting-control services"; INSTALL_ERRORS=0; install_dependencies || INSTALL_ERRORS=1; cleanup_legacy_units || INSTALL_ERRORS=1; create_systemd_service_unit_files || INSTALL_ERRORS=1; verify_systemd_service_unit_files || INSTALL_ERRORS=1; reload_systemd || INSTALL_ERRORS=1; if [ "$INSTALL_ERRORS" -eq 0 ]; then pass "Setting-control service installation is up to date"; else fail "Installation completed with errors; see $LOG_FILE"; fi; print_install_status; return "$INSTALL_ERRORS"; }; enable_ryzen_psic_workaround(){ init_colors; define_constants; systemctl reset-failed "$PACKAGE_C6_SERVICE" >/dev/null 2>&1 || :; if systemctl --quiet enable --now "$PACKAGE_C6_SERVICE"; then return 0; else log_unit_failure "$PACKAGE_C6_SERVICE"; fail "Failed to enable Package C6 workaround"; return 1; fi; }; disable_ryzen_psic_workaround(){ init_colors; define_constants; if systemctl --quiet disable --now "$PACKAGE_C6_SERVICE"; then return 0; else log_unit_failure "$PACKAGE_C6_SERVICE"; fail "Failed to restore Package C6 state"; return 1; fi; }; disable_ryzen_core_c6(){ init_colors; define_constants; systemctl reset-failed "$CORE_C6_SERVICE" >/dev/null 2>&1 || :; if systemctl --quiet enable --now "$CORE_C6_SERVICE"; then return 0; else log_unit_failure "$CORE_C6_SERVICE"; fail "Failed to disable Core C6"; return 1; fi; }; enable_ryzen_core_c6(){ init_colors; define_constants; if systemctl --quiet disable --now "$CORE_C6_SERVICE"; then return 0; else log_unit_failure "$CORE_C6_SERVICE"; fail "Failed to restore Core C6 state"; return 1; fi; }; disable_ryzen_boost(){ init_colors; define_constants; systemctl reset-failed "$BOOST_SERVICE" >/dev/null 2>&1 || :; if systemctl --quiet enable --now "$BOOST_SERVICE"; then return 0; else log_unit_failure "$BOOST_SERVICE"; fail "Failed to disable CPU boost"; return 1; fi; }; enable_ryzen_boost(){ init_colors; define_constants; if systemctl --quiet disable --now "$BOOST_SERVICE"; then return 0; else log_unit_failure "$BOOST_SERVICE"; fail "Failed to restore CPU boost"; return 1; fi; }; disable_aslr(){ init_colors; define_constants; systemctl reset-failed "$ASLR_SERVICE" >/dev/null 2>&1 || :; if systemctl --quiet enable --now "$ASLR_SERVICE"; then return 0; else log_unit_failure "$ASLR_SERVICE"; fail "Failed to disable ASLR"; return 1; fi; }; enable_aslr(){ init_colors; define_constants; if systemctl --quiet disable --now "$ASLR_SERVICE"; then return 0; else log_unit_failure "$ASLR_SERVICE"; fail "Failed to restore ASLR"; return 1; fi; }; ryzen_stabilizator_status(){ init_colors; define_constants; systemctl reset-failed "$STATUS_SERVICE" >/dev/null 2>&1 || :; systemctl start "$STATUS_SERVICE"; }; uninstall_ryzen_stabilizator(){ init_colors; define_constants; require_root || return 1; setup_log || return 1; info "Restoring controlled settings and removing service units"; for u in "$PACKAGE_C6_SERVICE" "$CORE_C6_SERVICE" "$BOOST_SERVICE" "$ASLR_SERVICE"; do if systemctl cat "$u" >/dev/null 2>&1; then systemctl --quiet disable --now "$u" >>"$LOG_FILE" 2>&1 || :; fi; done; rm -f "$SYSTEMD_DIR/$PACKAGE_C6_SERVICE" "$SYSTEMD_DIR/$CORE_C6_SERVICE" "$SYSTEMD_DIR/$BOOST_SERVICE" "$SYSTEMD_DIR/$ASLR_SERVICE" "$SYSTEMD_DIR/$STATUS_SERVICE"; reload_systemd; pass "Removed setting-control service units"; };
install_ryzen_stabilizator
enable_ryzen_psic_workaround
#disable_ryzen_core_c6
#disable_ryzen_boost
#disable_aslr
ryzen_stabilizator_status
```

<!-- END GENERATED PASTE-TO-RUN -->

## What this project is for

The project is aimed at systems where an AMD Family 17h processor—particularly early Ryzen/Summit Ridge systems—appears stable under ordinary stress testing but experiences silent Linux/Proxmox freezes associated with deep idle behavior. It provides runtime controls that can be applied independently, verified from the actual live hardware/kernel state, made persistent with normal systemd enablement, and reversed without inventing equivalent kernel command-line parameters.

The default call block enables only the Package C6 workaround. Core C6, CPU boost, and ASLR controls are present for controlled troubleshooting and are commented out by default.

This is a workaround toolkit, not a guarantee that every Family 17h freeze has the same cause. Disabling ASLR reduces security, and disabling CPU boost reduces peak CPU performance; both are optional diagnostic controls rather than recommended defaults.

## Quick status first

After installation, check the actual live state with:

```sh
systemctl start ryzen-stabilizator-status
```

Typical output looks like:

```text
=== Ryzen Stabilizator Status ===
Package C6  : DISABLED - Package-wide deep idle state; disabling it prevents package-level C6 entry.
Core C6     : ENABLED  - Per-core deep idle state; individual CPU cores may enter the CC6 low-power state.
CPU Boost   : ENABLED  - Allows CPU frequency to rise above its normal base operating frequency.
ASLR        : ENABLED  - Address-space randomization security feature. (randomize_va_space=2)
```

The status service reads the live MSRs, sysfs value, and sysctl value. It does not infer the displayed `ENABLED`/`DISABLED` state from whether a systemd unit is enabled; systemd state is only used to report a mismatch when a disable-control claims to be active but the live value disagrees.

## Installed service units

### `ryzen-stabilizator-status.service`

Runs an on-demand live status probe for all four controls. It prints colored output directly to the terminal that invoked `systemctl start ryzen-stabilizator-status` when that terminal can be identified, while also writing plain-text output to journald.

```sh
systemctl start ryzen-stabilizator-status
journalctl -t ryzen-stabilizator-status
```

### `amd-family17h-package-c6-disable.service`

Controls the Family 17h Package C6 enable bit through MSR `0xC0010292`, bit 32. The service first saves the relevant pre-change bit for each CPU under `/run`, performs a read-modify-write that clears only that bit, and verifies the actual MSR state afterward.

```sh
systemctl enable --now amd-family17h-package-c6-disable
systemctl disable --now amd-family17h-package-c6-disable
journalctl -t amd-family17h-package-c6-disable
```

`enable --now` applies the disable immediately and enables it for future boots. `disable --now` runs `ExecStop`, restores the state captured earlier in the current boot, and removes boot persistence.

### `amd-family17h-core-c6-disable.service`

Controls the Family 17h Core C6/CC6 bits in MSR `0xC0010296`. It clears bits 22, 14, and 6 while preserving all unrelated MSR bits, saves the original relevant bits per CPU, and restores them on stop.

```sh
systemctl enable --now amd-family17h-core-c6-disable
systemctl disable --now amd-family17h-core-c6-disable
journalctl -t amd-family17h-core-c6-disable
```

The service is guarded with `AuthenticAMD` and CPU family 23 (`17h`) checks before the MSR write is attempted. AMD documentation for Family 17h processors describes clearing bits 22, 14, and 6 of `MSRC001_0296` as a CC6-disable mechanism in documented errata; Family 17h includes more than first-generation Ryzen, so the presence of the mechanism does not imply that every Family 17h processor has the same stability problem.

### `cpu-boost-disable.service`

Uses the generic Linux CPUFreq system-wide boost control at `/sys/devices/system/cpu/cpufreq/boost` when that control is provided by the active scaling driver. A value of `0` disables frequency boost and `1` enables it.

```sh
systemctl enable --now cpu-boost-disable
systemctl disable --now cpu-boost-disable
journalctl -t cpu-boost-disable
```

This setting is not Ryzen-1-specific. The service refuses to apply the change if the global CPUFreq boost file is unavailable or not writable.

### `kernel-aslr-disable.service`

Uses the standard Linux `kernel.randomize_va_space` sysctl at `/proc/sys/kernel/randomize_va_space`. The service writes `0` to disable ASLR, records the original value (`0`, `1`, or `2`) for the current boot, and restores that exact value on stop.

```sh
systemctl enable --now kernel-aslr-disable
systemctl disable --now kernel-aslr-disable
journalctl -t kernel-aslr-disable
```

ASLR is a generic Linux security feature, not a Ryzen-specific CPU control. Disabling it weakens exploit mitigations and should normally be used only as a deliberate troubleshooting experiment.

## Convenience shell functions

The paste-to-run block defines wrappers around the service controls so the common operations are short and readable.

### Installation and removal

`install_ryzen_stabilizator` initializes color output and paths, requires root, prepares `/var/log/ryzen-stabilizator.log`, checks APT repositories, installs `msr-tools`, removes older unit names from previous iterations of the workaround, writes the five current unit files, verifies them with `systemd-analyze verify`, reloads systemd, and prints the installed control state.

`uninstall_ryzen_stabilizator` attempts to stop/disable each active disable-control first so its saved current-boot state can be restored, removes the unit files, and reloads systemd.

### Package C6 / PSIC workaround

```sh
enable_ryzen_psic_workaround
disable_ryzen_psic_workaround
```

`enable_ryzen_psic_workaround` is the default stability action. It maps to `systemctl enable --now amd-family17h-package-c6-disable.service` and therefore applies the MSR change immediately and on subsequent boots.

`disable_ryzen_psic_workaround` maps to `systemctl disable --now ...`, which stops the unit, restores the bit state saved earlier in the current boot, and removes future boot activation.

### Core C6

```sh
disable_ryzen_core_c6
enable_ryzen_core_c6
```

The first command enables the Core C6 disable-control immediately and persistently. The second removes that control and restores the saved current-boot CC6 bits.

### CPU boost

```sh
disable_ryzen_boost
enable_ryzen_boost
```

These functions disable or restore the kernel-exposed global CPU boost setting and make the selected disable-control persistent or non-persistent through systemd.

### ASLR

```sh
disable_aslr
enable_aslr
```

These functions disable or restore `randomize_va_space`. Because ASLR is a security mitigation, leaving `disable_aslr` commented out is the recommended default unless it is being tested intentionally.

### Status

```sh
ryzen_stabilizator_status
```

This wrapper resets any previous failure state on the status unit and starts `ryzen-stabilizator-status.service`. The service independently reads the actual live values instead of trusting the setting-control unit state.

## What the helper functions do

- `init_colors` enables ANSI colors only when standard output is a terminal and `NO_COLOR` is not set.
- `info`, `pass`, `warn`, and `fail` provide colored console messages and append plain-text installer messages to `/var/log/ryzen-stabilizator.log`.
- `define_constants` centralizes unit names, the systemd directory, the installer log, and APT backup location.
- `require_root` prevents installation from proceeding without root privileges.
- `setup_log` creates the installer log and makes it readable with mode `0644`.
- `require_msr_tools` checks for `rdmsr` and `wrmsr` before an MSR-dependent action is attempted.
- `unit_state` returns `systemctl is-enabled` state for the installation summary.
- `log_unit_failure` appends `systemctl status` and the most recent unit journal entries to the installer log after a wrapper failure.
- `reload_systemd` performs `systemctl daemon-reload` and records failures in the installer log.
- `remove_unsigned_repos` tests active APT source entries/stanzas individually using apt-secure behavior. Entries that produce signature/authentication failures are commented out, and the original files are backed up under `/var/backups/ryzen-stabilizator/apt`.
- `install_dependencies` runs the repository check and installs `msr-tools` quietly when it is not already installed.
- `cleanup_legacy_units` quietly removes obsolete unit names from earlier versions of this workaround.
- `create_package_c6_service`, `create_core_c6_service`, `create_boost_service`, `create_aslr_service`, and `create_status_service` generate the actual unit files under `/etc/systemd/system`.
- `create_systemd_service_unit_files` runs all five unit generators and aggregates any creation error.
- `verify_systemd_service_unit_files` validates every generated unit with `systemd-analyze verify` before use.
- `print_install_status` displays the four persistent control states and the status unit.
- `install_ryzen_stabilizator` orchestrates installation but does not itself choose optional Core C6, boost, or ASLR controls.
- `enable_ryzen_psic_workaround`, `disable_ryzen_psic_workaround`, `disable_ryzen_core_c6`, `enable_ryzen_core_c6`, `disable_ryzen_boost`, `enable_ryzen_boost`, `disable_aslr`, and `enable_aslr` are the human-friendly control wrappers.
- `ryzen_stabilizator_status` starts the aggregate live status service.
- `uninstall_ryzen_stabilizator` restores active controls where possible and removes the installed units.

## Default call block

The shipped `paste-to-run.sh` ends with:

```sh
install_ryzen_stabilizator
enable_ryzen_psic_workaround
#disable_ryzen_core_c6
#disable_ryzen_boost
#disable_aslr
ryzen_stabilizator_status
```

That means Package C6 is disabled by default while Core C6, CPU boost, and ASLR remain unchanged unless their lines are explicitly uncommented.

## Logging and state restoration

Installer activity is written to:

```text
/var/log/ryzen-stabilizator.log
```

Runtime service output is written to journald under each unit's `SyslogIdentifier`. The disable-control services save only the specific pre-change state they need under `/run`; because `/run` is per-boot volatile storage, this deliberately models “restore the state that existed before this service changed it during this boot.”

## APT repository handling

The script was designed for fresh Proxmox installations where subscription-only enterprise repositories can make `apt-get update` fail with authentication/signature errors. It tests each active `.list` line and Deb822 `.sources` stanza individually, comments out entries that fail the defined apt-secure/authentication checks, and stores the original source files under:

```text
/var/backups/ryzen-stabilizator/apt
```

Review this behavior before publishing or using the installer on hosts where repository policy is centrally managed.

## Family 17h scope

AMD Family 17h is broader than “Ryzen 1”: it includes multiple Zen-family product ranges. This project calls the MSR services `amd-family17h-*` because the unit guard checks CPU family 23 and because AMD documentation describes the relevant CC6 controls on Family 17h products; that naming should not be read as a claim that every Family 17h CPU needs this workaround.

The Package C6 and Core C6 controls are intentionally not presented as universal C-state MSRs. On non-Family-17h systems, the status service reports the two MSR controls as unsupported and the corresponding setter units fail their `ExecCondition` checks rather than writing unknown MSRs.

## References

- AMD Revision Guide for Family 17h Models 00h–0Fh: https://docs.amd.com/v/u/en-US/55449-PUB-1.21
- AMD Revision Guide for Family 17h Models 30h–3Fh, including documented CC6-disable bit programming: https://docs.amd.com/v/u/en-US/56323_PUB_1.03_RG_Rome
- Linux CPUFreq frequency boost documentation: https://www.kernel.org/doc/html/latest/admin-guide/pm/cpufreq.html
- Linux `randomize_va_space` documentation: https://docs.kernel.org/admin-guide/sysctl/kernel.html#randomize-va-space

## Keeping the README synchronized

`paste-to-run.sh` is the single source of truth. The clipboard helper fetches it directly, while the README code block is generated from it by:

```sh
python3 tools/sync_readme.py
```

For GitHub publication, `.github/workflows/sync-readme.yml` regenerates the README block from `paste-to-run.sh` and points the copy button at the repository's GitHub Pages helper. `.github/workflows/pages.yml` publishes `copy.html`; its JavaScript fetches `paste-to-run.sh` only when the button is clicked. Normal maintenance is therefore: edit `paste-to-run.sh`, then push it.

## Version

See [`VERSION`](VERSION) and [`CHANGELOG.md`](CHANGELOG.md). This archive is release **1.0.1**.
