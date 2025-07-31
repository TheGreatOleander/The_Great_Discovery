#!/usr/bin/env bash
set -e

# ===[ Config ]===
OUTPUT_DIR="$HOME/system_audit_$(date +%F_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "[*] Output directory: $OUTPUT_DIR"

# ===[ 0. Check for hardinfo2, prompt install if missing ]===
if ! command -v hardinfo2 &>/dev/null; then
    echo "[!] hardinfo2 is not installed."
    read -rp "Do you want to install hardinfo2 now? [Y/n] " response
    response=${response,,} # to lowercase
    if [[ "$response" =~ ^(yes|y| ) ]] || [[ -z "$response" ]]; then
        echo "[*] Installing hardinfo2..."
        sudo apt update
        sudo apt install -y hardinfo2
    else
        echo "[*] Skipping hardinfo2 system report."
        SKIP_HARDINFO2=true
    fi
fi

# ===[ 1. Run Hardinfo2 ]===
if [[ "$SKIP_HARDINFO2" != true ]]; then
    echo "[*] Running hardinfo2..."
    hardinfo2 -r -f html > "$OUTPUT_DIR/hardware_report.html"
    hardinfo2 -r -f txt > "$OUTPUT_DIR/hardware_report.txt"
fi

# ===[ 2. Generate Software/Env Audit ]===
echo "[*] Capturing software and environment info..."

# APT packages
dpkg --get-selections > "$OUTPUT_DIR/apt_installed.txt"

# Snap packages
snap list > "$OUTPUT_DIR/snap_installed.txt" 2>/dev/null || echo "No snapd found" > "$OUTPUT_DIR/snap_installed.txt"

# Flatpak packages
flatpak list --app > "$OUTPUT_DIR/flatpak_installed.txt" 2>/dev/null || echo "No flatpak found" > "$OUTPUT_DIR/flatpak_installed.txt"

# Pip (global)
pip3 freeze > "$OUTPUT_DIR/pip_global.txt" 2>/dev/null || echo "pip not found" > "$OUTPUT_DIR/pip_global.txt"

# Pyenv versions
if command -v pyenv &>/dev/null; then
  pyenv versions > "$OUTPUT_DIR/pyenv_versions.txt"
else
  echo "pyenv not found" > "$OUTPUT_DIR/pyenv_versions.txt"
fi

# Venvs
if [[ -d "$HOME/.venv" ]]; then
  source "$HOME/.venv/bin/activate"
  pip freeze > "$OUTPUT_DIR/pip_venv.txt"
  deactivate
fi

# System info
uname -a > "$OUTPUT_DIR/uname.txt"
lsb_release -a > "$OUTPUT_DIR/lsb_release.txt" 2>/dev/null || cat /etc/os-release > "$OUTPUT_DIR/lsb_release.txt"

# Crontab
crontab -l > "$OUTPUT_DIR/crontab.txt" 2>/dev/null || echo "No crontab for user" > "$OUTPUT_DIR/crontab.txt"

# UFW status
ufw status verbose > "$OUTPUT_DIR/ufw_status.txt" 2>/dev/null || echo "ufw not installed or inactive" > "$OUTPUT_DIR/ufw_status.txt"

# Aliases
alias > "$OUTPUT_DIR/aliases.txt"

# ===[ Done ]===
echo "[✓] Audit complete. Reports saved to: $OUTPUT_DIR"

# ===[ Optional: open HTML report ]===
if [[ -f "$OUTPUT_DIR/hardware_report.html" ]]; then
    read -rp "Open the hardware report in browser now? [Y/n] " view
    view=${view,,}
    if [[ "$view" =~ ^(yes|y| ) ]] || [[ -z "$view" ]]; then
        xdg-open "$OUTPUT_DIR/hardware_report.html" &>/dev/null &
    fi
fi
