#!/usr/bin/env bash
# ============================================================================
# teardown-firewall.sh
# ----------------------------------------------------------------------------
# Roll back everything setup-firewall.sh installed:
#   - removes custom sshd drop-in (reverts to port 22)
#   - removes iptables DNAT/MASQUERADE rules for the honeypot
#   - removes the HONEYPOT_ISOLATION chain
#   - disables UFW (does NOT purge rules — keeps history for audit)
# ============================================================================
set -Eeuo pipefail
IFS=$'\n\t'
if [[ $EUID -ne 0 ]]; then
  echo "ERROR: must run as root (sudo $0)" >&2
  exit 1
fi

echo "==> Removing sshd port-relocation drop-in"
rm -f /etc/ssh/sshd_config.d/99-honeypot-mgmt.conf
if sshd -t; then
  systemctl reload ssh || systemctl restart ssh
  echo "    sshd reverted to default port (22 unless SiteDefaults override)"
else
  echo "    sshd config invalid after removal; investigate manually."
fi

echo "==> Flushing NAT rules for honeypot"
# Delete the DNAT/MASQUERADE rules we added.  We match by port (:22, :8080, :554)
for DPORT in 22 8080 554; do
  while iptables -t nat -C PREROUTING -p tcp --dport "$DPORT" -j DNAT 2>/dev/null; do
    iptables -t nat -D PREROUTING -p tcp --dport "$DPORT" -j DNAT
  done
  while iptables -t nat -C POSTROUTING -p tcp --dport "$DPORT" -j MASQUERADE 2>/dev/null; do
    iptables -t nat -D POSTROUTING -p tcp --dport "$DPORT" -j MASQUERADE
  done
done

echo "==> Removing HONEYPOT_ISOLATION chain"
iptables -F HONEYPOT_ISOLATION 2>/dev/null || true
# Detach from FORWARD
while iptables -C FORWARD -i docker0           -j HONEYPOT_ISOLATION 2>/dev/null; do
  iptables -D FORWARD -i docker0           -j HONEYPOT_ISOLATION
done
while iptables -C FORWARD -i br-honeypot-net   -j HONEYPOT_ISOLATION 2>/dev/null; do
  iptables -D FORWARD -i br-honeypot-net   -j HONEYPOT_ISOLATION
done
iptables -X HONEYPOT_ISOLATION 2>/dev/null || true

echo "==> Removing persisted rules"
rm -f /etc/iptables/honeypot-isolation.rules.v4
netfilter-persistent save

echo "==> Disabling UFW (rules preserved)"
ufw --force disable

echo "==> Removing helper hook"
rm -f /usr/local/bin/honeypot-refresh-fwd.sh

echo "==> Done.  Verify with:  ss -tlnp | grep -E '(:22|:2200|:8080|:554)'"