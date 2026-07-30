# IoT Deception Honeypot

A low-interaction SSH honeypot that masquerades as a vulnerable IoT device (an
old IP camera / BusyBox appliance). It accepts **any** credentials, traps the
attacker in a fake shell, and logs everything to an embedded SQLite database.

> ⚠️ **Run only on networks you are authorized to monitor.** Never expose this
> directly to the public Internet without a network sensor in front of it.

## Tech Stack

| Concern        | Choice                                    |
|----------------|-------------------------------------------|
| Language       | Java 17                                   |
| Build          | Apache Maven 3.9+                         |
| SSH server     | Apache MINA SSHD 2.12.0                   |
| Persistence    | SQLite JDBC (org.xerial)                  |
| Logging        | SLF4J + Logback                           |
| Packaging      | Maven Shade Plugin (fat JAR)              |
| Container      | Eclipse Temurin JRE 17 Alpine             |

## Project Layout

```
iot-honeypot/
├── Dockerfile
├── pom.xml
├── README.md
└── src/main/
    ├── java/com/security/honeypot/
    │   ├── HoneypotServer.java     # Entry point: starts SSH on :2222
    │   ├── FakeShellFactory.java   # Canned BusyBox shell per session
    │   └── DatabaseManager.java    # SQLite schema + parameterized log helpers
    └── resources/
        └── logback.xml             # Console + honeypot.log appenders
```

## Build & Run

The easy way — one script handles Maven builds, fat-JAR bootstrapping, and
launching both the SSH server and the operator CLI.

### Windows

```bat
run.bat                :: build (if needed) and start the SSH server
run.bat logs 50        :: show last 50 auth attempts
run.bat commands 20    :: show last 20 shell commands
run.bat stats          :: summary
run.bat menu           :: interactive console
run.bat export a.csv   :: export all logs to CSV
run.bat reset          :: wipe logs (asks confirmation)
run.bat build          :: force a clean Maven build
run.bat docker         :: build + run the Docker image
```

### macOS / Linux

```bash
./run.sh                # build (if needed) and start the SSH server
./run.sh logs 50        # show last 50 auth attempts
./run.sh commands 20    # show last 20 shell commands
./run.sh stats          # summary
./run.sh menu           # interactive console
./run.sh export a.csv   # export all logs to CSV
./run.sh reset          # wipe logs (asks confirmation)
./run.sh build          # force a clean Maven build
./run.sh docker         # build + run the Docker image
```

### Manual (without the helper scripts)

```bash
cd iot-honeypot
mvn -B clean package
java -jar target/iot-honeypot.jar serve           # start SSH server
java -jar target/iot-honeypot.jar --stats         # summary
java -jar target/iot-honeypot.jar --logs 50       # last 50 auth attempts
java -jar target/iot-honeypot.jar --commands 20   # last 20 commands
java -jar target/iot-honeypot.jar --menu          # interactive console
java -jar target/iot-honeypot.jar --export a.csv all
java -jar target/iot-honeypot.jar --reset --yes
java -jar target/iot-honeypot.jar --help
```

Override port or bind address via system properties (the helper scripts
honor `HONEPOT_BIND` and `HONEPOT_PORT`):

```bash
java -Dhoneypot.port=2222 -Dhoneypot.bind=0.0.0.0 -jar target/iot-honeypot.jar
```

## Run with Docker

```bash
docker build -t iot-honeypot .
docker run --rm -p 2222:2222 -v honeypot-data:/data iot-honeypot
# then, in another shell, exec into the container or mount the volume:
docker run --rm -it -v honeypot-data:/data eclipse-temurin:17-jre-alpine \
    java -jar /data/iot-honeypot.jar --stats
```

The container persists `honeypot.db`, `hostkey.ser`, and `honeypot.log` into
the named volume `/data`.

## Talking to the Honeypot

Any SSH client works. The honeypot doesn't care what you type:

```bash
ssh -p 2222 root@localhost
# Password: literally anything
```

## Security Notes

- **All logins return `true`.** That's the trap. Without it, scanners would
  just bounce and we wouldn't learn anything.
- All inserts use `PreparedStatement` bind variables. Attacker-controlled
  strings never enter SQL via concatenation.
- The server binds to `0.0.0.0` by default; override with `-Dhoneypot.bind=...`.
- The Docker image runs as a non-root user; the listening port is
  unprivileged (2222) so root is unnecessary.
- Logs are written both to stdout and to `honeypot.log`. Rotate as needed.

### Sandbox Containment Audit (2026)

Every attacker-controlled input path enforces five rules. The
`Sanitizer` class is the single source of truth for scrub logic.

| Rule | Where it lives |
|------|----------------|
| 1. Zero native execution                          | `grep_search` audit: only `Runtime.getRuntime().addShutdownHook(...)` in `HoneypotServer`. No `Runtime.exec`, no `ProcessBuilder`, no `System.load*`, no JNI. |
| 2. Input sanitization & path-traversal strip      | `Sanitizer.cleanLine()` / `cleanValue()` — strips ANSI/CSI/OSC, control chars (incl. `\0`), `../`, `..\`, `%2e%2e/`. Applied in `FakeShellFactory`, all 6 `HttpHoneypot` handlers (`Login`, `ApiLogin`, `Dashboard`, `ApiStatus`, `ApiStream`, `ApiLock`, `Onvif`, `CatchAll`), and `RtspStub`. |
| 3. Prepared statements only                       | `DatabaseManager` uses `PreparedStatement` for every insert; `addColumnIfMissing` uses hardcoded identifier literals (SQLite DDL can't bind identifiers — annotated). CLI exports look up the operator-supplied table name in a `Map.of(...)` whitelist (`EXPORT_TABLES`) — never concatenated into SQL. |
| 4. Bounded memory per line (≤ 1024 chars)         | `FakeShellFactory.LineReader` and `RtspStub.BoundedLineReader` cap each line at `Sanitizer.MAX_LINE_LEN` (1024 bytes); overflow drains into a `Deque` so the next call resyncs. RTSP bodies capped at `MAX_VALUE_LEN`. |
| 5. No stack traces or class names leaked to attacker | All SSH/HTTP/RTSP handlers wrap their respond logic in `safeRespondTo` / static templates. Catch blocks log `e.getClass().getSimpleName()` (or just `debug`) instead of `e.getMessage()`. Internal errors never reach the wire. |

To re-verify any time:

* **Linux / macOS (bash)**:
  ```bash
  grep -nE 'Runtime\.exec|ProcessBuilder|System\.load' src/main/java/com/security/honeypot/*.java
  ```
* **Windows (PowerShell)**:
  ```powershell
  Select-String -Path src/main/java/com/security/honeypot/*.java -Pattern 'Runtime\.exec|ProcessBuilder|System\.load'
  ```

— should print nothing.

## Container Hardening

The `Dockerfile` and `docker-compose.yml` together implement defense-in-depth
on top of the JVM-side audit above.

### Rules applied

| Rule | Implementation |
|------|----------------|
| 1. Non-root execution         | `Dockerfile` creates uid `10001` (`adduser -u 10001 … -s /sbin/nologin`); `USER honeypot` before `ENTRYPOINT`. |
| 2. Read-only root FS          | `docker-compose.yml` sets `read_only: true`; only `/data` is writable via the named volume `honeypot-data`. `/tmp` and `/run` get bounded `tmpfs` mounts with `nosuid,nodev,noexec`. |
| 3. Drop all capabilities      | `cap_drop: [ALL]`; nothing is added back. Moby's `seccomp:default` profile is the syscall allowlist. |
| 4. Resource quotas            | `cpus: "0.5"`, `memory: 256M`, `pids_limit: 256`, `ulimits.nofile=4096/8192`. JVM matches with `-Xmx256m -XX:MaxRAMPercentage=75.0`. |
| 5. no-new-privileges          | `security_opt: [no-new-privileges:true]` plus `seccomp:default` and `apparmor:docker-default`. |

### Launch

```bash
# Build and start
docker compose up -d --build

# Verify the hardening landed
docker inspect iot-honeypot \
    | grep -E 'ReadonlyPaths|"CapDrop"|"NoNewPrivileges"|Memory'

# Watch a live attack
docker logs -f iot-honeypot
```

The named volume `honeypot-data` persists `honeypot.db`, `hostkey.ser`, and
`honeypot.log` across container restarts. Back it up periodically:

```bash
docker run --rm -v honeypot-data:/data -v $(pwd):/backup \
    alpine tar czf /backup/honeypot-data-$(date +%F).tgz /data
```

If you want to mount a host directory instead (so the data survives the
volume lifecycle), change the `volumes:` entry to
`/srv/honeypot/data:/data:rw,nosuid,nodev,noexec`.