package com.security.honeypot;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.time.OffsetDateTime;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * RtspStub
 *
 * A minimum-effort RTSP 1.0 listener that looks like a vendor camera
 * to opportunistic scanners (Shodan, Mirai variants). It answers
 * OPTIONS, DESCRIBE, and SETUP requests without ever actually
 * serving media. Everything that arrives is logged.
 *
 * This is not a full RTSP server — it is a honeypot that just
 * stays alive long enough to be probed, classified, and put on a
 * block list by attackers. That's the goal.
 */
public final class RtspStub {

    private static final Logger LOG = LoggerFactory.getLogger(RtspStub.class);

    private final int port;
    private final String bind;
    private volatile boolean running;
    private ServerSocket serverSocket;
    private ExecutorService executor;

    public RtspStub(int port, String bind) {
        this.port = port;
        this.bind = bind;
    }

    public int port() {
        return port;
    }

    public void start() throws IOException {
        executor = Executors.newCachedThreadPool();
        serverSocket = new ServerSocket();
        serverSocket.bind(new InetSocketAddress(bind, port));
        running = true;
        Thread accept = new Thread(this::acceptLoop, "rtsp-stub-accept");
        accept.setDaemon(true);
        accept.start();
        LOG.info("RTSP stub bound to {}:{}", bind, port);
    }

    public void stop() {
        running = false;
        try { if (serverSocket != null) serverSocket.close(); }
        catch (IOException ignored) { /* shutting down */ }
        if (executor != null) executor.shutdownNow();
    }

    private void acceptLoop() {
        while (running) {
            try {
                Socket client = serverSocket.accept();
                executor.submit(() -> handle(client));
            } catch (IOException e) {
                // Rule 5: avoid echoing exception messages into logs that
                // may be tailed by the operator.
                if (running) LOG.warn("RTSP accept failed (type={})", e.getClass().getSimpleName());
                return;
            }
        }
    }

    private void handle(Socket client) {
        try (Socket c = client) {
            String ip = c.getRemoteSocketAddress().toString();
            LOG.info("RTSP connection from {}", ip);

            try (InputStream in = c.getInputStream();
                 OutputStream out = c.getOutputStream()) {

                // Rule 2 + Rule 4: bounded line reader. We cap every
                // request line / header at Sanitizer.MAX_LINE_LEN bytes
                // so a malicious client cannot amplify memory or pass
                // through ANSI/OSC into SDP responses.
                BoundedLineReader reader = new BoundedLineReader(in);

                String line = reader.readLine();
                if (line == null) return;
                String[] parts = line.split(" ");
                if (parts.length < 2) {
                    respond(out, 400, "Bad Request", null);
                    return;
                }

                String method = Sanitizer.cleanValue(parts[0]);
                String target = Sanitizer.cleanValue(parts[1]);

                // Drain any headers, in case the client sends them.
                String cSeq = "1";
                String userAgent = null;
                int contentLength = 0;
                String clHeader = null;
                while ((line = reader.readLine()) != null && !line.isEmpty()) {
                    int colon = line.indexOf(':');
                    if (colon < 1) continue;
                    String name = line.substring(0, colon).trim();
                    String value = Sanitizer.cleanValue(
                            line.substring(colon + 1).trim());
                    if (name.equalsIgnoreCase("CSeq")) cSeq = value;
                    if (name.equalsIgnoreCase("User-Agent")) userAgent = value;
                    if (name.equalsIgnoreCase("Content-Length")) clHeader = value;
                }
                if (clHeader != null) {
                    try { contentLength = Integer.parseInt(clHeader); }
                    catch (NumberFormatException ignored) { /* invalid length */ }
                    // Cap RTSP body to Sanitizer.MAX_VALUE_LEN bytes so a
                    // bogus Content-Length cannot exhaust heap.
                    if (contentLength > 0 && contentLength <= Sanitizer.MAX_VALUE_LEN) {
                        byte[] body = in.readNBytes(contentLength);
                        LOG.info("RTSP body from {} ({} bytes)", ip, body.length);
                    }
                }

                LOG.info("RTSP {} {} from {} (UA={})",
                        method, target, ip, userAgent);

                switch (method) {
                    case "OPTIONS" -> respond(out, 200, "OK",
                            "Public: OPTIONS, DESCRIBE, SETUP, TEARDOWN\r\n");
                    case "DESCRIBE" -> respond(out, 200, "OK",
                            "Content-Type: application/sdp\r\n"
                                    + "\r\n"
                                    + sdpBody(target));
                    case "SETUP" -> respond(out, 200, "OK",
                            "Transport: RTP/AVP;unicast;client_port=8000-8001;"
                                    + "server_port=9000-9001\r\n"
                                    + "Session: " + randomSession() + "\r\n");
                    case "TEARDOWN" -> respond(out, 200, "OK", null);
                    default -> respond(out, 501, "Not Implemented", null);
                }
            }
        } catch (Exception e) {
            // Rule 5: never let exception messages / class names reach
            // the attacker's socket. Internal errors are debug-logged only.
            LOG.debug("RTSP client closed: {}", e.getClass().getSimpleName());
        }
    }

    private static void respond(OutputStream out, int code, String reason,
                                String extraHeaders) throws IOException {
        String headers = "RTSP/1.0 " + code + " " + reason + "\r\n"
                + "CSeq: 1\r\n"
                + "Server: IPCAM RTSP/1.0\r\n"
                + "Date: " + OffsetDateTime.now() + "\r\n";
        if (extraHeaders != null) {
            headers += extraHeaders;
        }
        headers += "\r\n";
        out.write(headers.getBytes(StandardCharsets.US_ASCII));
        out.flush();
    }

    private static String sdpBody(String url) {
        return """
            v=0
            o=- %d %d IN IP4 %s
            s=IPCamera Stream
            c=IN IP4 0.0.0.0
            t=0 0
            m=video 0 RTP/AVP 96
            a=rtpmap:96 H264/90000
            a=control:%s
            a=mimetype:string;"video/mpeg"
            """.formatted(System.currentTimeMillis(),
                          System.currentTimeMillis(),
                          "127.0.0.1", url);
    }

    private static String randomSession() {
        return Long.toHexString(System.nanoTime());
    }

    /**
     * Like {@link InputStreamReader}-then-line, but every returned line
     * is capped at {@link Sanitizer#MAX_LINE_LEN} bytes; anything beyond
     * is drained up to the next {@code \n} so the next call returns fresh
     * data and we don't allocate a giant buffer. This is the canonical
     * Rule-4 pattern.
     */
    private static final class BoundedLineReader {
        private final InputStream in;
        private final byte[] buf = new byte[Sanitizer.MAX_LINE_LEN];
        private final java.util.ArrayDeque<Integer> overflow = new java.util.ArrayDeque<>();
        private int pos;
        private boolean crSeen;
        private boolean closed;

        BoundedLineReader(InputStream in) { this.in = in; }

        String readLine() throws IOException {
            if (closed) return null;
            pos = 0;
            crSeen = false;
            while (!overflow.isEmpty()) {
                int b = overflow.poll();
                if (b == -1) { closed = true; return null; }
                if (!appendByte(b)) return finishLine();
            }
            int b;
            while ((b = in.read()) != -1) {
                if (b == '\n') return finishLine();
                if (b == '\r') { crSeen = true; continue; }
                if (crSeen) crSeen = false;
                if (!appendByte(b)) {
                    while ((b = in.read()) != -1 && b != '\n') overflow.add(b);
                    return finishLine();
                }
            }
            closed = true;
            return pos == 0 && overflow.isEmpty() ? null : finishLine();
        }

        private boolean appendByte(int b) {
            if (pos >= buf.length) return false;
            buf[pos++] = (byte) b;
            return true;
        }

        private String finishLine() {
            String line = new String(buf, 0, pos, StandardCharsets.US_ASCII);
            crSeen = false;
            return line;
        }
    }
}
