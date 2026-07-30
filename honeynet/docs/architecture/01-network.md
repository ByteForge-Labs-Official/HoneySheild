# Network Topology

## Goal

Funnel every attacker probe into a chosen honeypot, capture packets for IDS,
and prevent the honeypot from initiating outbound connections.

## Docker networks

```yaml
networks:
  edge_net:       { driver: bridge, internal: false }   # internet-attached
  honeypot_net:   { driver: bridge, internal: true  }   # no gateway
  data_net:       { driver: bridge, internal: true  }
  mgmt_net:       { driver: bridge, internal: true  }
```

* `edge_net` carries Traefik + MQTT bridge ports.
* `honeypot_net` is **internal: true** — containers on it have no default route,
  can't reach the internet, but can still receive connections on published ports.
* The host iptables rules (in `deploy/hardening/firewall/`) install an additional
  belt-and-braces egress block on top of Docker's internal network property, in
  case a misconfigured compose file accidentally attaches a honeypot to an
  external network.

## Host firewall (UFW + iptables)

See [`deploy/hardening/firewall/setup-firewall.sh`](../../deploy/hardening/firewall/setup-firewall.sh)
and its teardown twin. Summary of rules:

| Chain | Rule | Why |
|---|---|---|
| `ufw user-input` | `allow 2200/tcp` | keep admin SSH alive |
| `ufw user-input` | `deny 22/tcp` | close default SSH |
| `nat:PREROUTING` | `tcp --dport {ssh,http,rtsp,modbus} → honeypot` | forward bait ports |
| `filter:OUTPUT` | owner match `uid-owner 10001` → `REJECT` | block honeypot egress |
| `filter:OUTPUT` | `-d 127/8,10/8,172.16/12,192.168/16` → `REJECT` | prevent loopback sniffs |

## Recommended DNS posture

* Use an external registrar with **DNSSEC** enabled.
* Publish only the relevant bait ports — for example, do not expose port 22 even
  if you run an SSH cowrie; instead run a service that imitates IoT-firmware
  login panels.
* Run a dedicated subdomain `mgmt.example.com` that resolves only to the host
  management interface and is not advertised anywhere.

## Health-check & watchdog

* `deploy/scripts/watchdog.sh` polls Docker health checks every minute.  If a
  honeypot dies, it triggers `honeypot-refresh-fwd.sh` to refresh DNAT against
  the new container IP (Docker reassigns on recreation).
