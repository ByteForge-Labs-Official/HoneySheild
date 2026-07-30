#!/usr/bin/env bash
# run.sh -- convenience launcher for the IoT Honeypot
# Usage:
#   ./run.sh                -> build (if needed) and start the SSH server
#   ./run.sh logs 50        -> show last 50 auth attempts
#   ./run.sh commands 20    -> show last 20 shell commands
#   ./run.sh stats          -> summary
#   ./run.sh menu           -> interactive console
#   ./run.sh export a.csv   -> export all logs to CSV
#   ./run.sh reset          -> wipe logs (asks confirmation)
#   ./run.sh build          -> force a clean Maven build
#   ./run.sh docker         -> build + run the Docker image
set -euo pipefail

JAR="target/iot-honeypot.jar"
CMD="${1:-serve}"

if [[ ! -f "$JAR" || "$CMD" == "build" || "$CMD" == "docker" ]]; then
  case "$CMD" in
    docker)
      echo "Building Docker image 'iot-honeypot'..."
      docker build -t iot-honeypot .
      echo "Starting container (Ctrl+C to stop)..."
      docker run --rm -p 2222:2222 -v honeypot-data:/data iot-honeypot
      exit 0
      ;;
    build|"")
      echo "Building fat JAR..."
      mvn -B -ntp clean package
      JAR="target/iot-honeypot.jar"
      [[ "$CMD" == "build" || "$CMD" == "" ]] && exit 0
      ;;
  esac
fi

exec java -Dhoneypot.bind="${HONEPOT_BIND:-0.0.0.0}" \
          -Dhoneypot.port="${HONEPOT_PORT:-2222}" \
          -jar "$JAR" "$@"
