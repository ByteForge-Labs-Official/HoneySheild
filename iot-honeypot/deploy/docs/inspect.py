import yaml, json
d = yaml.safe_load(open("deploy/docker-compose.yml", "r", encoding="utf-8"))
for n, s in d["services"].items():
    ports = s.get("ports") or []
    nets = s.get("networks") or []
    vols = s.get("volumes") or []
    sec = s.get("secrets") or []
    ro = any("ro" in str(v) for v in vols)
    cap = s.get("cap_drop") or []
    rlim = (s.get("deploy") or {}).get("resources", {}).get("limits", {})
    print(f"{n:22} ports={ports} nets={nets} vols={len(vols)} ro_vols={ro} secrets={len(sec)} cap_drop={cap} cpu={rlim.get('cpus')} mem={rlim.get('memory')}")