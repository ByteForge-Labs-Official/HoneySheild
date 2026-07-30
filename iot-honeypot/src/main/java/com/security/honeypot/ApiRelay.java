package com.security.honeypot;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicReference;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * ApiRelay
 *
 * Forwards live honeypot events captured by the Java SSH server
 * to the FastAPI backend at http://localhost:8000/api/v1/events/{hpId}/events
 * so that the React SOC dashboard shows real-time SSH attacks.
 */
public final class ApiRelay {

    private static final Logger LOG = Logger.getLogger(ApiRelay.class.getName());

    private static final String BASE_URL = System.getProperty("honeypot.api.url", "http://localhost:8000/api/v1");

    private static final String FALLBACK_HP_ID = "d18ed9b6-eb11-43ed-911e-2e2dcf52359d";

    private static final AtomicReference<String> HP_ID = new AtomicReference<>(null);

    private static final HttpClient CLIENT = HttpClient.newBuilder()
            .version(java.net.http.HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(3))
            .build();

    private static final ExecutorService POOL = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "api-relay");
        t.setDaemon(true);
        return t;
    });

    public static void main(String[] args) throws Exception {
        System.out.println("Testing ApiRelay...");
        sendAuthEvent("127.0.0.1", "root", "123456", "ssh");
        sendCommandEvent("127.0.0.1", "uname -a", "ssh");
        Thread.sleep(2000);
    }

    private ApiRelay() {
    }

    public static void sendAuthEvent(String ip, String username, String password, String protocol) {
        String json = "{\"event_type\":\"brute_force\",\"protocol\":\"" + esc(protocol) + "\","
                + "\"src_ip\":\"" + esc(ip) + "\",\"src_port\":2222,\"dst_port\":2222,"
                + "\"payload\":{\"username\":\"" + esc(username) + "\","
                + "\"password\":\"" + esc(password) + "\",\"country\":\"LOCAL\"}}";
        push(json, "AUTH ip=" + ip + " user=" + username);
    }

    public static void sendCommandEvent(String ip, String command, String protocol) {
        String json = "{\"event_type\":\"command\",\"protocol\":\"" + esc(protocol) + "\","
                + "\"src_ip\":\"" + esc(ip) + "\",\"src_port\":2222,\"dst_port\":2222,"
                + "\"payload\":{\"command\":\"" + esc(command) + "\",\"country\":\"LOCAL\"}}";
        push(json, "CMD ip=" + ip + " cmd=" + command);
    }

    private static void push(final String json, final String label) {
        POOL.submit(() -> {
            try {
                String hpId = resolveHoneypotId();
                String url = BASE_URL + "/events/" + hpId + "/events";
                HttpRequest req = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .header("Content-Type", "application/json")
                        .timeout(Duration.ofSeconds(4))
                        .POST(HttpRequest.BodyPublishers.ofString(json))
                        .build();
                HttpResponse<String> res = CLIENT.send(req, HttpResponse.BodyHandlers.ofString());
                LOG.info("[RELAY->DASHBOARD] " + label + " => HTTP " + res.statusCode() + " BODY: " + res.body());
            } catch (Exception e) {
                LOG.fine("[RELAY] Backend unreachable: " + e.getMessage());
            }
        });
    }

    private static String resolveHoneypotId() {
        String cached = HP_ID.get();
        if (cached != null)
            return cached;
        try {
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + "/honeypots"))
                    .timeout(Duration.ofSeconds(3))
                    .GET()
                    .build();
            HttpResponse<String> res = CLIENT.send(req, HttpResponse.BodyHandlers.ofString());
            String body = res.body();
            int idx = body.indexOf("\"id\":\"");
            if (idx >= 0) {
                int start = idx + 6;
                int end = body.indexOf('"', start);
                if (end > start) {
                    String id = body.substring(start, end);
                    HP_ID.set(id);
                    LOG.info("[RELAY] Resolved honeypot ID: " + id);
                    return id;
                }
            }
        } catch (Exception e) {
            LOG.log(Level.FINE, "[RELAY] Could not fetch honeypot ID: " + e.getMessage());
        }
        HP_ID.set(FALLBACK_HP_ID);
        return FALLBACK_HP_ID;
    }

    private static String esc(String raw) {
        if (raw == null)
            return "";
        return raw.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
    }
}
