package com.security.honeypot;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;

/**
 * HttpHoneypot
 *
 * A low-interaction web admin panel that mimics IoT device UIs. It:
 *   - Serves a profile-appropriate login page (router / camera / door lock).
 *   - Records every POST'd credential pair.
 *   - Serves a "dashboard" after bait-login so attackers keep poking.
 *   - Responds to ONVIF/RTSP REST-style paths with believable JSON.
 *   - Traps crawlers hitting obvious vuln paths (/.env, /admin.php).
 */
public final class HttpHoneypot {

    private static final Logger LOG = LoggerFactory.getLogger(HttpHoneypot.class);

    private final int port;
    private final String bind;
    private final DeviceProfile profile;
    private final HttpServer server;

    public HttpHoneypot(int port, String bind, DeviceProfile profile) throws IOException {
        this.port = port;
        this.bind = bind;
        this.profile = profile;
        this.server = HttpServer.create(new InetSocketAddress(bind, port), 64);
        this.server.setExecutor(Executors.newFixedThreadPool(8));

        registerRoutes();
        LOG.info("HTTP honeypot ({}) bound to {}:{}", profile, bind, port);
    }

    public void start() {
        server.start();
    }

    public void stop() {
        server.stop(0);
    }

    public int port() {
        return port;
    }

    private void registerRoutes() {
        // Login surface (the bait)
        server.createContext("/login.htm",    new LoginHandler());
        server.createContext("/login.html",   new LoginHandler());
        server.createContext("/login.php",    new LoginHandler());
        server.createContext("/cgi-bin/login.cgi", new LoginHandler());
        server.createContext("/api/login",    new ApiLoginHandler());

        // Post-login fake dashboards (per profile)
        server.createContext("/index.htm",    new DashboardHandler());
        server.createContext("/index.html",   new DashboardHandler());
        server.createContext("/home.htm",     new DashboardHandler());

        // Camera/doorlock JSON surface
        server.createContext("/api/status",   new ApiStatusHandler());
        server.createContext("/api/stream",   new ApiStreamHandler());
        server.createContext("/api/lock",     new ApiLockHandler());

        // ONVIF-style device discovery
        server.createContext("/onvif/device_service", new OnvifHandler());

        // Catch-all for "/" and any unregistered path.
        server.createContext("/", new CatchAllHandler());
    }

    // -----------------------------------------------------------------------
    //  Handlers
    // -----------------------------------------------------------------------

    /** Renders the vendor-themed login page and eats credentials on POST. */
    private class LoginHandler implements HttpHandler {
        @Override public void handle(HttpExchange ex) throws IOException {
            String ip = clientIp(ex);
            // Rule 2: scrub header values before they're stored or logged.
            String ua = Sanitizer.cleanValue(header(ex, "User-Agent"));
            String method = ex.getRequestMethod();

            if ("POST".equalsIgnoreCase(method)) {
                FormData form = readForm(ex);
                String user = Sanitizer.cleanValue(form.getOrDefault("username",
                                form.getOrDefault("user", form.getOrDefault("name", ""))));
                String pass = Sanitizer.cleanValue(form.getOrDefault("password",
                                form.getOrDefault("pass", form.getOrDefault("pwd", ""))));
                LOG.info("HTTP LOGIN ip={} user='{}' pass='{}'", ip, user, pass);
                DatabaseManager.logAuth(ip, user, pass, "http");
                DatabaseManager.logHttpRequest(ip, "POST",
                        Sanitizer.cleanValue(ex.getRequestURI().getPath()),
                        ua, user, pass, 302);
                // Always "succeed" -> send them to the dashboard.
                ex.getResponseHeaders().add("Location", "/index.htm");
                respond(ex, 302, "", "text/html");
                return;
            }

            DatabaseManager.logHttpRequest(ip, "GET",
                    Sanitizer.cleanValue(ex.getRequestURI().getPath()),
                    ua, null, null, 200);
            respond(ex, 200, loginPage(profile), "text/html; charset=utf-8");
        }
    }

    /** JSON login endpoint that some vendors expose for their mobile app. */
    private class ApiLoginHandler implements HttpHandler {
        @Override public void handle(HttpExchange ex) throws IOException {
            String ip = clientIp(ex);
            String ua = Sanitizer.cleanValue(header(ex, "User-Agent"));
            if (!"POST".equalsIgnoreCase(ex.getRequestMethod())) {
                DatabaseManager.logHttpRequest(ip, ex.getRequestMethod(),
                        Sanitizer.cleanValue(ex.getRequestURI().getPath()),
                        ua, null, null, 405);
                respond(ex, 405, "{\"error\":\"method_not_allowed\"}", "application/json");
                return;
            }
            FormData form = readForm(ex);
            String user = Sanitizer.cleanValue(form.getOrDefault("username", ""));
            String pass = Sanitizer.cleanValue(form.getOrDefault("password", ""));
            LOG.info("API LOGIN ip={} user='{}' pass='{}'", ip, user, pass);
            DatabaseManager.logAuth(ip, user, pass, "http");
            DatabaseManager.logHttpRequest(ip, "POST",
                    Sanitizer.cleanValue(ex.getRequestURI().getPath()),
                    ua, user, pass, 200);

            String body = """
                {"status":"ok","token":"%s","role":"admin","device":"%s"}
                """.formatted(fakeToken(), profile.name().toLowerCase());
            respond(ex, 200, body, "application/json");
        }
    }

    /** Fake "everything's fine" dashboard so the attacker lingers. */
    private class DashboardHandler implements HttpHandler {
        @Override public void handle(HttpExchange ex) throws IOException {
            String ip = clientIp(ex);
            String ua = Sanitizer.cleanValue(header(ex, "User-Agent"));
            DatabaseManager.logHttpRequest(ip, "GET",
                    Sanitizer.cleanValue(ex.getRequestURI().getPath()),
                    ua, null, null, 200);
            respond(ex, 200, dashboard(profile), "text/html; charset=utf-8");
        }
    }

    /** Generic telemetry/status JSON. */
    private class ApiStatusHandler implements HttpHandler {
        @Override public void handle(HttpExchange ex) throws IOException {
            String ip = clientIp(ex);
            String ua = Sanitizer.cleanValue(header(ex, "User-Agent"));
            DatabaseManager.logHttpRequest(ip, "GET",
                    Sanitizer.cleanValue(ex.getRequestURI().getPath()),
                    ua, null, null, 200);
            String body = switch (profile) {
                case CAMERA   -> """
                    {"device":"IPCAM-7201","fw":"V5.4.5","uptime":1234567,"online":true,"stream":"rtsp://%s:554/Streaming/Channels/101"}
                    """.formatted(ex.getLocalAddress().getHostName());
                case DOORLOCK -> """
                    {"device":"SmartLock-A1","fw":"1.2.7","battery":87,"state":"locked","lastEvent":"unlock_denied"}
                    """;
                case ROUTER   -> """
                    {"device":"SOHO-Router","fw":"V2.0.1","wan_ip":"203.0.113.42","connected_clients":3}
                    """;
                default       -> """
                    {"status":"ok","ts":"%s"}
                    """.formatted(OffsetDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME));
            };
            respond(ex, 200, body, "application/json");
        }
    }

    /** Stream metadata endpoint (used by camera profiles). */
    private class ApiStreamHandler implements HttpHandler {
        @Override public void handle(HttpExchange ex) throws IOException {
            String ip = clientIp(ex);
            String ua = Sanitizer.cleanValue(header(ex, "User-Agent"));
            DatabaseManager.logHttpRequest(ip, "GET",
                    Sanitizer.cleanValue(ex.getRequestURI().getPath()),
                    ua, null, null, 200);
            respond(ex, 200, """
                {"channels":[{"id":101,"name":"MainStream","resolution":"1920x1080","codec":"H264","rtsp":"rtsp://%s:554/Streaming/Channels/101"},{"id":102,"name":"SubStream","resolution":"640x360","codec":"H264","rtsp":"rtsp://%s:554/Streaming/Channels/102"}]}
                """.formatted(ex.getLocalAddress().getHostName(), ex.getLocalAddress().getHostName()),
                    "application/json");
        }
    }

    /** Door-lock control — accepts any command; never actually moves a bolt. */
    private class ApiLockHandler implements HttpHandler {
        @Override public void handle(HttpExchange ex) throws IOException {
            String ip = clientIp(ex);
            String ua = Sanitizer.cleanValue(header(ex, "User-Agent"));
            FormData form = readForm(ex);
            String action = Sanitizer.cleanValue(form.getOrDefault("action", "lock"));
            String pin    = Sanitizer.cleanValue(form.getOrDefault("pin",    ""));
            LOG.info("LOCK CMD ip={} action={} pin='{}'", ip, action, pin);
            DatabaseManager.logAuth(ip, "lock:" + action, pin, "http");
            DatabaseManager.logHttpRequest(ip, "POST",
                    Sanitizer.cleanValue(ex.getRequestURI().getPath()),
                    ua, action, pin, 200);
            respond(ex, 200, """
                {"status":"queued","action":"%s","accepted":true,"note":"pin validation pending"}
                """.formatted(action), "application/json");
        }
    }

    /** ONVIF device_service: responds with minimal SOAP body so scanners stay happy. */
    private class OnvifHandler implements HttpHandler {
        @Override public void handle(HttpExchange ex) throws IOException {
            String ip = clientIp(ex);
            String ua = Sanitizer.cleanValue(header(ex, "User-Agent"));
            DatabaseManager.logHttpRequest(ip, "POST",
                    Sanitizer.cleanValue(ex.getRequestURI().getPath()),
                    ua, null, null, 200);
            String body = """
                <?xml version="1.0" encoding="UTF-8"?>
                <Envelope xmlns="http://www.w3.org/2003/05/soap-envelope">
                  <Body>
                    <GetDeviceInformationResponse>
                      <Manufacturer>GenericVendor</Manufacturer>
                      <Model>IPCAM-7201</Model>
                      <FirmwareVersion>5.4.5</FirmwareVersion>
                      <SerialNumber>SN00000000</SerialNumber>
                      <HardwareId>1.0</HardwareId>
                    </GetDeviceInformationResponse>
                  </Body>
                </Envelope>
                """;
            respond(ex, 200, body, "application/soap+xml; charset=utf-8");
        }
    }

    /** Behaviors for any path we don't explicitly handle. */
    private static class CatchAllHandler implements HttpHandler {
        // Known scanner fingerprints — pretend we found something juicy.
        private static final List<String> SENSITIVE_PATHS = List.of(
                "/.env", "/.git/config", "/admin.php", "/wp-login.php",
                "/phpmyadmin", "/shell.php", "/config.xml", "/credentials.txt");

        @Override public void handle(HttpExchange ex) throws IOException {
            String ip = clientIp(ex);
            String ua = Sanitizer.cleanValue(header(ex, "User-Agent"));
            // Path goes into LOG/DB only — strip ANSI/control chars and
            // cap length before persisting (Rule 2).
            String path = Sanitizer.cleanValue(
                    ex.getRequestURI().getPath()).toLowerCase();

            // Root: send attackers to the login page.
            if ("/".equals(path)) {
                ex.getResponseHeaders().add("Location", "/login.htm");
                respond(ex, 302, "<html><body>Redirecting to <a href=\"/login.htm\">login</a>.</body></html>",
                        "text/html");
                return;
            }

            if (SENSITIVE_PATHS.contains(path)) {
                LOG.info("Sensitive path probed: {} from {}", path, ip);
                DatabaseManager.logHttpRequest(ip, ex.getRequestMethod(), path, ua,
                        null, null, 200);
                // Tempt them with a fake leak.
                String body = switch (path) {
                    case "/.env" -> """
                        APP_ENV=production
                        DB_HOST=10.0.0.5
                        DB_USER=admin
                        DB_PASS=hunter2
                        APP_KEY=base64:c29tZS1zdXBlci1zZWNyZXQ=
                        AWS_ACCESS_KEY_ID=AKIAFAKEFAKEFAKEFAKE
                        """;
                    case "/credentials.txt" ->
                            "admin:admin\nroot:toor\nuser:12345\nservice:ServiceP@ss";
                    default -> "<!-- TODO: harden -->";
                };
                respond(ex, 200, body, "text/plain; charset=utf-8");
                return;
            }

            DatabaseManager.logHttpRequest(ip, ex.getRequestMethod(), path, ua,
                    null, null, 404);
            respond(ex, 404, """
                <html><head><title>404</title></head>
                <body><h1>Not Found</h1>
                <p>The requested URL was not found on this server.</p></body></html>
                """, "text/html; charset=utf-8");
        }
    }

    // -----------------------------------------------------------------------
    //  HTML templates
    // -----------------------------------------------------------------------

    private static String loginPage(DeviceProfile profile) {
        String title = switch (profile) {
            case ROUTER   -> "SOHO Router - Login";
            case CAMERA   -> "IP Camera - Web Admin";
            case DOORLOCK -> "SmartLock - Owner Console";
            default       -> "Web Admin";
        };
        String product = profile.displayName;
        return """
            <!doctype html><html><head>
              <meta charset="utf-8"><title>%s</title>
              <style>body{font-family:Arial,sans-serif;background:#1c1f24;color:#eee;margin:40px}
              .box{max-width:340px;margin:auto;padding:24px;background:#2a2f36;border-radius:6px}
              h1{font-size:18px;margin:0 0 8px;color:#9ad}
              .p{font-size:12px;color:#9ab}
              input{display:block;width:100%%;margin:8px 0;padding:8px;border:1px solid #444;background:#1c1f24;color:#eee}
              button{background:#2563eb;color:#fff;border:0;padding:9px 14px;cursor:pointer;border-radius:4px;width:100%%}
              .f{font-size:11px;color:#888;margin-top:10px}</style></head>
            <body><div class="box">
              <h1>%s</h1>
              <div class="p">%s</div>
              <form method="post">
                <input name="username" placeholder="Username" autofocus>
                <input name="password" type="password" placeholder="Password">
                <button type="submit">Sign in</button>
              </form>
              <div class="f">v5.4.5 &middot; &copy; GenericVendor</div>
            </div></body></html>
            """.formatted(title, title, product);
    }

    private static String dashboard(DeviceProfile profile) {
        String title = switch (profile) {
            case ROUTER   -> "Router Status";
            case CAMERA   -> "Live Camera Dashboard";
            case DOORLOCK -> "Door Lock Console";
            default       -> "Device Dashboard";
        };
        String body = switch (profile) {
            case CAMERA   -> """
                <p><b>Stream:</b> rtsp://%(host)s:554/Streaming/Channels/101</p>
                <p><b>Motion Detection:</b> Enabled</p>
                <p><b>Night Mode:</b> Auto</p>
                <p><b>Last Event:</b> 2026-07-27 21:14 motion @ Front Door</p>
                """;
            case DOORLOCK -> """
                <p><b>Battery:</b> 87%%</p>
                <p><b>State:</b> LOCKED</p>
                <p><b>Last Unlock:</b> admin @ 2026-07-26 08:02</p>
                <p><b>Failed Attempts:</b> 3</p>
                """;
            case ROUTER   -> """
                <p><b>WAN IP:</b> 203.0.113.42</p>
                <p><b>LAN:</b> 192.168.1.0/24</p>
                <p><b>Connected clients:</b> 3</p>
                <p><b>Uptime:</b> 47 days</p>
                """;
            default       -> """
                <p><b>Status:</b> OK</p>
                <p><b>Uptime:</b> 12h</p>
                """;
        };
        return """
            <!doctype html><html><head>
              <meta charset="utf-8"><title>%s</title>
              <style>body{font-family:Arial,sans-serif;background:#1c1f24;color:#eee;margin:30px}
              h1{color:#9ad;font-size:18px}
              .card{background:#2a2f36;border-radius:6px;padding:18px;max-width:480px}
              a{color:#7df}</style></head>
            <body><div class="card">
              <h1>%s</h1>
              %s
              <hr>
              <p><a href="/api/status">/api/status</a> &middot;
                 <a href="/api/stream">/api/stream</a> &middot;
                 <a href="/api/lock">/api/lock</a></p>
            </div></body></html>
            """.formatted(title, title, body);
    }

    // -----------------------------------------------------------------------
    //  Helpers
    // -----------------------------------------------------------------------

    private static String header(HttpExchange ex, String name) {
        return ex.getRequestHeaders().getFirst(name);
    }

    private static String clientIp(HttpExchange ex) {
        // Prefer X-Forwarded-For if behind a sensor/proxy, fall back to socket.
        String fwd = header(ex, "X-Forwarded-For");
        if (fwd != null && !fwd.isBlank()) return fwd.split(",")[0].trim();
        return ex.getRemoteAddress().getAddress().getHostAddress();
    }

    private static FormData readForm(HttpExchange ex) throws IOException {
        FormData out = new FormData();
        try (InputStream in = ex.getRequestBody()) {
            byte[] body = in.readAllBytes();
            if (body.length == 0) return out;
            String raw = new String(body, StandardCharsets.UTF_8);
            for (String pair : raw.split("&")) {
                int eq = pair.indexOf('=');
                if (eq < 0) continue;
                String k = urlDecode(pair.substring(0, eq));
                String v = urlDecode(pair.substring(eq + 1));
                out.put(k, v);
            }
        }
        return out;
    }

    private static String urlDecode(String s) {
        return URLDecoder.decode(s.replace("+", "%2B"), StandardCharsets.UTF_8)
                .replace("%2B", "+");
    }

    private static void respond(HttpExchange ex, int status, String body, String contentType)
            throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", contentType);
        ex.getResponseHeaders().set("Server", "nginx/1.14.0 (GenericVendor)");
        ex.sendResponseHeaders(status, bytes.length);
        try (OutputStream os = ex.getResponseBody()) {
            os.write(bytes);
        }
    }

    private static String fakeToken() {
        return java.util.UUID.randomUUID().toString().replace("-", "");
    }

    /** Simple ordered multi-map for form bodies. Keeps last-write-wins. */
    private static class FormData extends LinkedHashMap<String, String> {
        @Override public String put(String key, String value) {
            return super.put(key, value);
        }
    }

    /** Visible for {@link CatchAllHandler} usage; unused otherwise. */
    @SuppressWarnings("unused")
    private static List<String> asciiBanner() {
        return Arrays.asList(
            " ____                        _   _   _      _   ",
            "|  _ \\ ___  _ __  _   ___  __| | | |_| |__  | |_ ",
            "| |_) / _ \\| '_ \\| | | \\ \\/ /| | | __| '_ \\ | __|",
            "|  __/ (_) | | | | |_| |>  < | |_| |_| | | || |_ ",
            "|_|   \\___/|_| |_|\\__,_/_/\\_\\ \\___/|___|_| |_|\\__|"
        );
    }
}