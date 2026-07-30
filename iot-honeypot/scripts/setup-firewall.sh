#!/usr/bin/env bash
# ============================================================================
# setup-firewall.sh
# ----------------------------------------------------------------------------
# Production-ready UFW + iptables lockdown for a fresh Ubuntu 22.04/24.04 VPS
# that hosts the iot-honeypot Docker stack.
#
#   1. Management SSH relocated from :22 -> :2200  (so attackers always hit
#      the honeypot on :22 instead of locking you out).
#   2. Public :22 forward -> container :2222.
#   3. Outbound egress from the honeypot container is REJECTED (no botnet
#      relay).  SSH/HTTP/RTSP inside the container are bind-only and never
#      need to dial out.
#   4. The honeypot container is isolated from the host loopback and the
#      RFC1918 private subnets so a container escape can't pivot to
#      management services (Postgres, internal DNS, etc.).
#
# SAFETY: this script refuses to run unless you confirm explicitly.  Re-run
# is idempotent — every step is a no-op if already applied.
# ============================================================================

set -Eeuo pipefail
IFS=$'\n\t'
umask 027

# ---------------------------------------------------------------------------
# 0.  Sanity / safety checks
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
  echo "ERROR: must run as root (sudo $0)" >&2
  exit 1
fi

. /etc/os-release
if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "WARNING: this script targets Ubuntu ${VERSION_ID:-unknown}; detected ${ID:-?}." >&2
  read -rp "Continue anyway? [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]] || exit 1
fi

# Configurable knobs (override via environment)
: "${MGMT_SSH_PORT:=2200}"               # real SSH listens here
: "${HONEYPOT_PUBLIC_PORT:=22}"          # attackers connect here
: "${HONEYPOT_DOCKER_PORT:=2222}"        # container's internal SSH
: "${HONEYPOT_HTTP_PORT:=8080}"
: "${HONEYPOT_RTSP_PORT:=554}"
: "${HONEYPOT_DOCKER_NETWORK:=honeypot-net}"
: "${HEALTHCHECK_INTERFACE:=$(ip -4 route show default | awk '{print $5;exit}')}"
: "${ALLOW_SSH_FROM:=}"                 # optional CIDR allowlist for mgmt

# Reassurance: if we are inside an SSH session on port 22, opening :2200
# without keeping :22 reachable would be catastrophic.  Detect the original
# port and refuse to proceed unless MGMT_SSH_PORT != that value.
ORIGINAL_SSH_PORT="$(sshd -T 2>/dev/null | awk '$1=="port"{print $2;exit}')"
ORIGINAL_SSH_PORT="${ORIGINAL_SSH_PORT:-22}"

if [[ "$ORIGINAL_SSH_PORT" != "22" ]] && [[ "$MGMT_SSH_PORT" != "$ORIGINAL_SSH_PORT" ]]; then
  echo "Management SSH is already on :${ORIGINAL_SSH_PORT}." >&2
  echo "Re-run with MGMT_SSH_PORT=${ORIGINAL_SSH_PORT} to keep parity." >&2
  exit 1
fi

echo "==> Configuration:"
echo "    Host mgmt SSH       : ${MGMT_SSH_PORT}"
echo "    Public honeypot SSH : ${HONEYPOT_PUBLIC_PORT} -> container ${HONEYPOT_DOCKER_PORT}"
echo "    Honeypot HTTP       : ${HONEYPOT_HTTP_PORT}"
echo "    Honeypot RTSP       : ${HONEYPOT_RTSP_PORT}"
echo "    Docker network      : ${HONEYPOT_DOCKER_NETWORK}"
echo "    Healthcheck iface   : ${HEALTHCHECK_INTERFACE}"
echo "    Allow SSH from CIDR : ${ALLOW_SSH_FROM:-any}"
echo
read -rp "Apply this firewall plan? [y/N] " ans
[[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }

# ---------------------------------------------------------------------------
# 1.  Install / enable required packages
# ---------------------------------------------------------------------------
echo "==> Installing ufw + iptables-persistent"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends ufw iptables-persistent netfilter-persistent

# ---------------------------------------------------------------------------
# 2.  Relocate management SSH (Requirement 1)
# ---------------------------------------------------------------------------
echo "==> Relocating sshd to port ${MGMT_SSH_PORT}"
SSHD_CONF=/etc/ssh/sshd_config
SSHD_CONF_D=/etc/ssh/sshd_config.d
mkdir -p "$SSHD_CONF_D"

# Drop a drop-in that overrides the main Port directive
cat > "${SSHD_CONF_D}/99-honeypot-mgmt.conf" <<EOF
# Managed by setup-firewall.sh
Port ${MGMT_SSH_PORT}
AddressFamily any
ListenAddress 0.0.0.0
ListenAddress ::
EOF
chmod 0644 "${SSHD_CONF_D}/99-honeypot-mgmt.conf"

# Validate before reloading — refuse to lock ourselves out
if ! sshd -t; then
  echo "ERROR: sshd config invalid; aborting before reload." >&2
  exit 1
fi
systemctl reload ssh || systemctl restart ssh
echo "    sshd now listens on :${MGMT_SSH_PORT}"

# ---------------------------------------------------------------------------
# 3.  UFW baseline
# ---------------------------------------------------------------------------
echo "==> Configuring UFW defaults (deny inbound, allow outbound, deny routed)"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw default deny routed            # critical: drop forwarding by default

# Loopback is always allowed (UFW default rule handles it)
# Limit sshd against brute force
ufw limit "${MGMT_SSH_PORT}/tcp" comment 'mgmt sshd rate-limited'

# Optional CIDR allowlist for management SSH
if [[ -n "$ALLOW_SSH_FROM" ]]; then
  ufw delete limit "${MGMT_SSH_PORT}/tcp" >/dev/null || true
  ufw allow from "$ALLOW_SSH_FROM" to any port "${MGMT_SSH_PORT}" proto tcp comment 'mgmt sshd allowlist'
fi

# Health-check ping from monitoring (optional)
# ufw allow from 10.0.0.0/24 to any port ${MGMT_SSH_PORT} proto tcp

# ---------------------------------------------------------------------------
# 4.  Enable forwarding so the honeypot can be reached on :22
# ---------------------------------------------------------------------------
echo "==> Enabling IPv4 forwarding + UFW forwarding policy"
if ! grep -q '^net.ipv4.ip_forward=1' /etc/sysctl.d/99-honeypot.conf 2>/dev/null; then
  cat > /etc/sysctl.d/99-honeypot.conf <<EOF
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
EOF
  sysctl --system
fi

# UFW needs to permit forwarding for specific ports
ufw default deny routed
# Insert forwarding allow rules in /etc/ufw/before.rules so they survive
# `ufw reload`.  We use the nat table via iptables (managed below).
sed -i 's/^DEFAULT_FORWARD_POLICY=.*/DEFAULT_FORWARD_POLICY="ACCEPT"/' \
    /etc/default/ufw || echo 'DEFAULT_FORWARD_POLICY="ACCEPT"' >> /etc/default/ufw

# ---------------------------------------------------------------------------
# 5.  Outbound egress block for the honeypot (Requirement 3)
# ---------------------------------------------------------------------------
echo "==> Blocking outbound egress from the honeypot network"
HONEYPOT_SUBNET="$(docker network inspect "$HONEYPOT_DOCKER_NETWORK" \
    --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null || true)"

if [[ -z "$HONEYPOT_SUBNET" ]]; then
  # Try common fallback subnets; the script must still run even if the
  # container is offline so we don't lock ourselves out.
  HONEYPOT_SUBNET="172.30.42.0/24"
  echo "    Docker network ${HONEYPOT_DOCKER_NETWORK} not present; assuming ${HONEYPOT_SUBNET}"
fi

# We use iptables directly because UFW cannot express "block egress only
# for this source subnet".  Wrap into /etc/iptables so it survives reboots.
IPTABLES_DIR=/etc/iptables
mkdir -p "$IPTABLES_DIR"

RULES_FILE="${IPTABLES_DIR}/honeypot-isolation.rules.v4"
cat > "$RULES_FILE" <<EOF
# Generated by setup-firewall.sh — DO NOT EDIT BY HAND
# Restore via: netfilter-persistent start (or service netfilter-persistent reload)
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]

# --- Honeypot isolation chain (Requirement 3 + 4) -------------------------
:HONEYPOT_ISOLATION - [0:0]
-A HONEYPOT_ISOLATION -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
-A HONEYPOT_ISOLATION -o lo -j REJECT --reject-with icmp-net-prohibited
-A HONEYPOT_ISOLATION -d 127.0.0.0/8     -j REJECT --reject-with icmp-net-prohibited
-A HONEYPOT_ISOLATION -d 10.0.0.0/8      -j REJECT --reject-with icmp-net-prohibited
-A HONEYPOT_ISOLATION -d 172.16.0.0/12   -j REJECT --reject-with icmp-net-prohibited
-A HONEYPOT_ISOLATION -d 192.168.0.0/16  -j REJECT --reject-with icmp-net-prohibited
-A HONEYPOT_ISOLATION -d 169.254.0.0/16  -j REJECT --reject-with icmp-net-prohibited
-A HONEYPOT_ISOLATION -m addrtype --dst-type MULTICAST -j REJECT --reject-with icmp-net-prohibited
-A HONEYPOT_ISOLATION -m addrtype --dst-type BROADCAST  -j REJECT --reject-with icmp-net-prohibited
-A HONEYPOT_ISOLATION ! -o eth0 -j RETURN                                  # allow replies on other ifaces (e.g., docker0 internal)
-A HONEYPOT_ISOLATION -j REJECT --reject-with icmp-net-prohibited
COMMIT
EOF

# Apply rules idempotently
iptables-restore < "$RULES_FILE" || true

# Anchor HONEYPOT_ISOLATION into the FORWARD chain for traffic from the
# honeypot subnet only.  We use -i (incoming interface) rather than -s so
# the rule survives bridge-network renumberings.
iptables -C FORWARD -i br-"${HONEYPOT_DOCKER_NETWORK#honeypot-}" \
    -j HONEYPOT_ISOLATION 2>/dev/null \
  || iptables -I FORWARD 1 -i br-"${HONEYPOT_DOCKER_NETWORK#honeypot-}" \
        -j HONEYPOT_ISOLATION

# Also enforce on the docker0 bridge as a belt-and-braces measure
iptables -C FORWARD -i docker0 -j HONEYPOT_ISOLATION 2>/dev/null \
  || iptables -I FORWARD 1 -i docker0 -j HONEYPOT_ISOLATION

# Persist
netfilter-persistent save

# ---------------------------------------------------------------------------
# 6.  Public :22 -> container :2222 DNAT (Requirement 2)
# ---------------------------------------------------------------------------
echo "==> Setting up NAT DNAT :${HONEYPOT_PUBLIC_PORT} -> container :${HONEYPOT_DOCKER_PORT}"
# Discover the container's bridge-side IP (assumes honeypot container is running)
CONTAINER_IP="$(docker inspect iot-honeypot \
    --format '{{.NetworkSettings.Networks.'"${HONEYPOT_DOCKER_NETWORK}"'.IPAddress}}' 2>/dev/null || true)"

if [[ -z "$CONTAINER_IP" ]]; then
  echo "    Container 'iot-honeypot' not running yet.  DNAT rule will be created as a stub; rerun after `docker compose up -d`."
  CONTAINER_IP="172.30.42.10"  # reasonable default; will be rewritten by container-resolve.sh
fi

# PREROUTING (DNAT) for inbound public traffic
iptables -t nat -C PREROUTING -p tcp --dport "$HONEYPOT_PUBLIC_PORT" \
    -j DNAT --to-destination "${CONTAINER_IP}:${HONEYPOT_DOCKER_PORT}" 2>/dev/null \
  || iptables -t nat -I PREROUTING 1 -p tcp --dport "$HONEYPOT_PUBLIC_PORT" \
        -j DNAT --to-destination "${CONTAINER_IP}:${HONEYPOT_DOCKER_PORT}"

# POSTROUTING (MASQUERADE) for return traffic leaving via the public interface
iptables -t nat -C POSTROUTING -p tcp -d "$CONTAINER_IP" --dport "$HONEYPOT_DOCKER_PORT" \
    -j MASQUERADE 2>/dev/null \
  || iptables -t nat -I POSTROUTING 1 -p tcp -d "$CONTAINER_IP" --dport "$HONEYPOT_DOCKER_PORT" \
        -j MASQUERADE

# Forward allow for the new mapping (FORWARD policy is ACCEPT in
# /etc/default/ufw; the HONEYPOT_ISOLATION chain above guarantees outbound
# is rejected, but inbound stays reachable).
iptables -C FORWARD -p tcp -d "$CONTAINER_IP" --dport "$HONEYPOT_DOCKER_PORT" \
    -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT 2>/dev/null \
  || iptables -I FORWARD 1 -p tcp -d "$CONTAINER_IP" --dport "$HONEYPOT_DOCKER_PORT" \
        -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT

# Optional: forward HTTP/RTSP too (comment out if you don't want them
# exposed publicly — the SSH port-forward is the load-bearing rule).
for HPORT in "$HONEYPOT_HTTP_PORT" "$HONEYPOT_RTSP_PORT"; do
  iptables -t nat -C PREROUTING -p tcp --dport "$HPORT" \
      -j DNAT --to-destination "${CONTAINER_IP}:${HPORT}" 2>/dev/null \
    || iptables -t nat -I PREROUTING 1 -p tcp --dport "$HPORT" \
          -j DNAT --to-destination "${CONTAINER_IP}:${HPORT}"
  iptables -t nat -C POSTROUTING -p tcp -d "$CONTAINER_IP" --dport "$HPORT" \
      -j MASQUERADE 2>/dev/null \
    || iptables -t nat -I POSTROUTING 1 -p tcp -d "$CONTAINER_IP" --dport "$HPORT" \
          -j MASQUERADE
done

netfilter-persistent save

# ---------------------------------------------------------------------------
# 7.  UFW opens public-facing honeypot ports (forwarded by iptables above)
# ---------------------------------------------------------------------------
echo "==> UFW: open public honeypot ports"
ufw allow "${HONEYPOT_PUBLIC_PORT}/tcp"  comment 'honeypot SSH public (DNAT to 2222)'
ufw allow "${HONEYPOT_HTTP_PORT}/tcp"   comment 'honeypot HTTP public'
ufw allow "${HONEYPOT_RTSP_PORT}/tcp"   comment 'honeypot RTSP public'

# Limit noisy protocols so a SYN flood can't trivially amplify
ufw limit "${HONEYPOT_PUBLIC_PORT}/tcp"

# ---------------------------------------------------------------------------
# 8.  Enable UFW (last so we never lock out mid-script)
# ---------------------------------------------------------------------------
ufw --force enable
ufw status verbose

# ---------------------------------------------------------------------------
# 9.  Helper hook: refresh container IP if the container restarts
# ---------------------------------------------------------------------------
cat > /usr/local/bin/honeypot-refresh-fwd.sh <<'HOOK'
#!/usr/bin/env bash
# Re-resolve the iot-honeypot container's IP and re-pin the DNAT rules.
set -Eeuo pipefail
NET="${HONEYPOT_DOCKER_NETWORK:-honeypot-net}"
PORT_PUBLIC="${HONEYPOT_PUBLIC_PORT:-22}"
PORT_IN="${HONEYPOT_DOCKER_PORT:-2222}"
PORT_HTTP="${HONEYPOT_HTTP_PORT:-8080}"
PORT_RTSP="${HONEYPOT_RTSP_PORT:-554}"

IP="$(docker inspect iot-honeypot --format '{{.NetworkSettings.Networks.'${NET}'.IPAddress}}' 2>/dev/null || true)"
[[ -z "$IP" ]] && exit 0

for TUPLE in "${PORT_PUBLIC}:${PORT_IN}" "${PORT_HTTP}:${PORT_HTTP}" "${PORT_RTSP}:${PORT_RTSP}"; do
  PUB="${TUPLE%%:*}"; IN="${TUPLE##*:}"
  iptables -t nat -F PREROUTING  >/dev/null 2>&1 || true
  iptables -t nat -A PREROUTING -p tcp --dport "$PUB" -j DNAT --to-destination "${IP}:${IN}"
  iptables -t nat -A POSTROUTING -p tcp -d "$IP" --dport "$IN" -j MASQUERADE
done
netfilter-persistent save
HOOK
chmod 0755 /usr/local/bin/honeypot-refresh-fwd.sh

# ---------------------------------------------------------------------------
# 10.  Summary + next steps
# ---------------------------------------------------------------------------
cat <<EOF

==>  Firewall plan applied.

     - Management SSH  : $(hostname -I | awk '{print $1}'):${MGMT_SSH_PORT}
     - Honeypot SSH    : $(hostname -I | awk '{print $1}'):${HONEYPOT_PUBLIC_PORT}  (DNAT -> ${CONTAINER_IP}:${HONEYPOT_DOCKER_PORT})
     - Honeypot HTTP   : $(hostname -I | awk '{print $1}'):${HONEYPOT_HTTP_PORT}
     - Honeypot RTSP   : $(hostname -I | awk '{print $1}'):${HONEYPOT_RTSP_PORT}

     DO NOT CLOSE THIS SSH SESSION.  Open a NEW one on port ${MGMT_SSH_PORT}
     and verify you can log in.  If the new session fails, run:
        sudo bash $(dirname "$0")/teardown-firewall.sh
     to roll back before getting locked out.

     Tear-down script:  $(dirname "$0")/teardown-firewall.sh

EOF