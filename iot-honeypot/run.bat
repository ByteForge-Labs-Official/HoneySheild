@echo off
setlocal enabledelayedexpansion
if "%JAVA_HOME%"=="" set "JAVA_HOME=C:\Program Files\Java\jdk-18.0.2.1"
REM -- run.bat -- convenience launcher for the IoT Honeypot
REM
REM Usage:
REM   run.bat                       build (if needed) and start the SSH server
REM   run.bat as <camera|router|...> start with a device profile
REM   run.bat logs 50               show last 50 auth attempts
REM   run.bat commands 20           show last 20 shell commands
REM   run.bat requests 20           show last 20 HTTP requests
REM   run.bat stats                 summary
REM   run.bat menu                  interactive console
REM   run.bat export out.csv        export all logs to CSV
REM   run.bat reset                 wipe logs (asks confirmation)
REM   run.bat build                 force a clean Maven build
REM   run.bat docker                build + run the Docker image

set JAR=target\iot-honeypot.jar
set CMD=%1
if "%CMD%"=="" set CMD=serve

REM -- Default the bind/port env vars so missing config does not become
REM    an empty -D property (which crashes Integer.parseInt in static init).
if "%HONEPOT_BIND%"=="" set HONEPOT_BIND=0.0.0.0
if "%HONEPOT_PORT%"=="" set HONEPOT_PORT=2222

if "%CMD%"=="as" (
    if "%2"=="" (
        echo Profile required after 'as'. Example: run.bat as camera
        exit /b 2
    )
    set "JAVA_OPTS=!JAVA_OPTS! -Dhoneypot.profile=%2"
    set "CMD=serve"
)

if not exist "%JAR%" goto :build
if /I "%CMD%"=="build" goto :build
if /I "%CMD%"=="docker" goto :docker

:run
java -Dhoneypot.bind=%HONEPOT_BIND% -Dhoneypot.port=%HONEPOT_PORT% !JAVA_OPTS! -jar %JAR% %*
goto :eof

:build
echo Building fat JAR...
call mvnw.cmd -B -ntp clean package
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)
if /I "%CMD%"=="build" goto :eof
goto :run

:docker
echo Building Docker image 'iot-honeypot'...
call docker build -t iot-honeypot .
if errorlevel 1 exit /b 1
echo Starting container (Ctrl+C to stop)...
call docker run --rm -p 2222:2222 -p 8080:8080 -p 554:554 -v honeypot-data:/data iot-honeypot
goto :eof