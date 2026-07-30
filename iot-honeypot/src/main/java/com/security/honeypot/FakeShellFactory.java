package com.security.honeypot;

import org.apache.sshd.server.Environment;
import org.apache.sshd.server.ExitCallback;
import org.apache.sshd.server.channel.ChannelSession;
import org.apache.sshd.server.command.Command;
import org.apache.sshd.server.shell.ShellFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * FakeShellFactory
 *
 * Implements MINA SSHD's Command/Runnable contract so each SSH
 * session gets a believable, low-interaction BusyBox-style shell.
 *
 * All "outputs" are hardcoded; the honeypot never actually runs
 * attacker input. Every command is recorded for forensics.
 */
public class FakeShellFactory implements ShellFactory {

    @Override
    public Command createShell(ChannelSession channel) {
        return new FakeShell(channel);
    }

    /**
     * FakeShell
     *
     * One instance per SSH channel. Reads lines from the client,
     * writes canned responses to stdout, and exits cleanly on
     * exit/quit or stream EOF.
     */
    public static class FakeShell implements Command, Runnable {

        private static final Logger LOG = LoggerFactory.getLogger(FakeShell.class);

        private final ChannelSession channel;
        private InputStream in;
        private OutputStream out;
        private OutputStream err;
        private ExitCallback callback;
        private Environment env;
        private Thread ioThread;

        public FakeShell(ChannelSession channel) {
            this.channel = channel;
        }

        public FakeShell() {
            this(null);
        }

        // Canned outputs keyed on the *exact* command. Lower-cased.
        private static final Map<String, String> RESPONSES = new ConcurrentHashMap<>();

        static {
            RESPONSES.put("whoami", "root");
            RESPONSES.put("id", "uid=0(root) gid=0(root) groups=0(root)");
            RESPONSES.put("hostname", "ipcam");
            RESPONSES.put("uname -a",
                    "Linux ipcam 2.6.32 #1 SMP Wed Jan 12 14:15:00 CST 2015 mips GNU/Linux");
            RESPONSES.put("uptime",
                    " 11:42:00 up 47 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01");
            RESPONSES.put("ifconfig",
                    "eth0      Link encap:Ethernet  HWaddr 00:11:22:33:44:55\n"
                            + "          inet addr:192.168.1.110  Bcast:192.168.1.255  Mask:255.255.255.0\n"
                            + "          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1");
            RESPONSES.put("pwd", "/root");
            RESPONSES.put("ls", "bin   dev   etc   home   lib   proc   root   sbin   tmp   usr   var");
            RESPONSES.put("ls -la",
                    "drwxr-xr-x   2 root   root    4096 May  4  2018 bin\n"
                            + "drwxr-xr-x   3 root   root    4096 May  4  2018 etc\n"
                            + "drwx------   2 root   root    4096 May  4  2018 root");
            RESPONSES.put("cat /etc/passwd",
                    "root:x:0:0:root:/root:/bin/sh\n"
                            + "admin:x:0:0:root:/root:/bin/sh\n"
                            + "support:x:500:500:Linux User,,,:/home/support:/bin/sh\n"
                            + "nobody:x:65534:65534:nobody:/nonexistent:/bin/false");
            RESPONSES.put("cat /etc/shadow",
                    "root:$1$z3xQ9b8P$LtKlxY6gZ4o8eH1u7c9Wq/:17000:0:99999:7:::\n"
                            + "admin:$1$z3xQ9b8P$LtKlxY6gZ4o8eH1u7c9Wq/:17000:0:99999:7:::");
            RESPONSES.put("ps", "  PID TTY          TIME CMD\n"
                    + "    1 ?        00:00:01 init\n"
                    + "  213 ?        00:00:00 telnetd\n"
                    + "  214 ?        00:00:00 httpd\n"
                    + "  317 ?        00:00:00 dropbear\n"
                    + "  401 pts/0    00:00:00 sh");
        }

        @Override
        public void setInputStream(InputStream in) {
            this.in = in;
        }

        @Override
        public void setOutputStream(OutputStream out) {
            this.out = out;
        }

        @Override
        public void setErrorStream(OutputStream err) {
            this.err = err;
        }

        @Override
        public void setExitCallback(ExitCallback callback) {
            this.callback = callback;
        }

        @Override
        public void start(ChannelSession channel, Environment env) throws IOException {
            this.env = env;
            this.ioThread = new Thread(this, "honeypot-shell-" + Long.toHexString(channel.getChannelId()));
            this.ioThread.start();
        }

        @Override
        public void run() {
            String ip = clientIp();
            try {
                writeBanner();
                writePrompt();

                // Rule 4: stream-based reader with a hard 1024-byte buffer per line.
                // An attacker that pushes gigabytes of garbage cannot exhaust memory.
                LineReader lines = new LineReader(in, out, Sanitizer.MAX_LINE_LEN);

                String line;
                while ((line = lines.nextLine()) != null) {
                    // Rule 2: scrub ANSI escapes, control chars, null bytes, and
                    // path-traversal sequences before any logging or echo.
                    String cmd = Sanitizer.cleanLine(line);
                    if (cmd.isEmpty()) {
                        writePrompt();
                        continue;
                    }

                    // Forensics first — always persist before answering.
                    DatabaseManager.logCommand(ip, cmd);

                    String lower = cmd.toLowerCase();
                    if ("exit".equals(lower) || "quit".equals(lower)
                            || "logout".equals(lower)) {
                        write("logout\r\n");
                        break;
                    }

                    // Rule 5: never reflect Java exceptions or class names.
                    // respondTo() returns a generic sh-style message; any error
                    // inside it is swallowed (logged operator-side).
                    String response = safeRespondTo(cmd, lower);
                    if (response != null) {
                        write(response);
                    }

                    writePrompt();
                }
            } catch (Exception e) {
                // Rule 5: do not leak stack traces or class names back to the
                // attacker. Log them server-side only.
                LOG.debug("Shell IO ended for {}: {}", ip, e.getMessage());
            } finally {
                if (callback != null) {
                    callback.onExit(0);
                }
            }
        }

        /**
         * Wraps {@link #respondTo} so any internal exception is converted
         * to the standard sh "command not found" message. Rule 5.
         */
        private String safeRespondTo(String cmd, String lower) {
            try {
                return respondTo(cmd, lower);
            } catch (Exception e) {
                // Never echo raw exception messages into logs that may be
                // tail-visible; only the exception type for diagnostics.
                LOG.warn("respondTo failure for cleaned-cmd (type={})",
                        e.getClass().getSimpleName());
                return "sh: " + Sanitizer.cleanLine(cmd) + ": command not found\r\n";
            }
        }

        /** Best-effort client IP from the channel session; falls back to 127.0.0.1. */
        private String clientIp() {
            if (channel != null && channel.getServerSession() != null) {
                try {
                    java.net.SocketAddress remote = channel.getServerSession().getClientAddress();
                    if (remote instanceof java.net.InetSocketAddress) {
                        java.net.InetSocketAddress isa = (java.net.InetSocketAddress) remote;
                        if (isa.getAddress() != null) {
                            return isa.getAddress().getHostAddress();
                        }
                    }
                } catch (Exception ignored) {
                    // fall through
                }
            }
            if (env != null) {
                try {
                    String peer = env.getEnv().get("SSH_CLIENT");
                    if (peer != null && !peer.isBlank()) {
                        return peer.split("\\s+")[0];
                    }
                } catch (Exception ignored) {
                    // fall through
                }
            }
            return "127.0.0.1";
        }

        private void writeBanner() throws IOException {
            write("Welcome to BusyBox v1.20.2 (2018-03-12 11:20:00 UTC)\r\n\r\n");
            write("System initialization completed.\r\n");
        }

        private void writePrompt() throws IOException {
            write("root@ipcam:~# ");
        }

        private void write(String s) throws IOException {
            out.write(s.getBytes(StandardCharsets.UTF_8));
            out.flush();
        }

        /**
         * Resolve the canned response for a command.
         * Simulates wget/curl behavior then denies permission.
         */
        private String respondTo(String cmd, String lower) {
            // Exact match
            String exact = RESPONSES.get(lower);
            if (exact != null) {
                return exact + "\r\n";
            }

            // Pretend wget/curl ran, then deny.
            if (lower.startsWith("wget ") || lower.equals("wget")) {
                return "--2026-07-27 10:00:00--  http://example.com/payload.sh\r\n"
                        + "Resolving example.com... 93.184.216.34\r\n"
                        + "Connecting to example.com|93.184.216.34|:80... connected.\r\n"
                        + "HTTP request sent, awaiting response... 200 OK\r\n"
                        + "Length: 1024 (1.0K) [application/x-sh]\r\n"
                        + "Saving to: 'payload.sh'\r\n\r\n"
                        + "payload.sh             100%[===================>]   1.00K  --.-K/s   in 0.01s\r\n\r\n"
                        + "2026-07-27 10:00:01 (110 KB/s) - 'payload.sh' saved [1024/1024]\r\n"
                        + "sh: 1: payload.sh: Permission denied\r\n";
            }
            if (lower.startsWith("curl ") || lower.equals("curl")) {
                return "  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\r\n"
                        + "                                 Dload  Upload   Total   Spent    Left  Speed\r\n"
                        + "100  1024  100  1024    0     0   110k      0 --:--:-- --:--:-- --:--:--  110k\r\n"
                        + "sh: 1: cannot execute binary file: Permission denied\r\n";
            }

            // Generic fallback: standard sh error format.
            return "sh: " + cmd + ": command not found\r\n";
        }

        @Override
        public void destroy(ChannelSession channel) {
            if (ioThread != null) {
                ioThread.interrupt();
            }
        }
    }

    /**
     * LineReader
     *
     * Reads one logical line at a time from an arbitrary InputStream with
     * a hard byte cap per line. Streams longer than {@code maxBytes} are
     * truncated and the remainder is discarded — the attacker doesn't get
     * to consume unbounded heap just by typing forever.
     *
     * Bytes are interpreted as UTF-8; incomplete multi-byte sequences at
     * the truncation boundary are dropped.
     */
    static final class LineReader {

        private final InputStream in;
        private final OutputStream out;
        private final int maxBytes;
        private boolean lastWasCr = false;
        private boolean inEscape = false;

        LineReader(InputStream in, OutputStream out, int maxBytes) {
            this.in = in;
            this.out = out;
            this.maxBytes = maxBytes;
        }

        String nextLine() throws IOException {
            ByteArrayBuilder b = new ByteArrayBuilder(maxBytes + 1);
            int read;
            while ((read = in.read()) >= 0) {
                // 1. Handle CRLF safely
                if (read == '\n' && lastWasCr) {
                    lastWasCr = false;
                    continue; // Skip LF if it immediately follows CR
                }
                lastWasCr = (read == '\r');

                // 2. Process Enter (\r or \n)
                if (read == '\r' || read == '\n') {
                    if (out != null) {
                        out.write(new byte[] { '\r', '\n' });
                        out.flush();
                    }
                    return b.toUtf8();
                }

                // 3. Handle Escape sequences (e.g., arrow keys)
                if (read == 27) {
                    inEscape = true;
                    continue;
                }
                if (inEscape) {
                    if ((read >= 'a' && read <= 'z') || (read >= 'A' && read <= 'Z') || read == '~') {
                        inEscape = false; // end of escape sequence
                    }
                    continue; // drop escape chars so they don't corrupt the terminal
                }

                // 4. Handle backspace (DEL=127 or BS=8)
                if (read == 127 || read == 8) {
                    if (!b.isEmpty()) {
                        b.len--;
                        if (out != null) {
                            out.write(new byte[] { 8, ' ', 8 });
                            out.flush();
                        }
                    }
                    continue;
                }

                // 5. Echo only printable characters
                if (out != null && read >= 32 && read <= 126) {
                    out.write(read);
                    out.flush();
                }

                if (!b.append((byte) read)) {
                    // Cap exceeded — drain to end-of-line, then return
                    drainRemaining();
                    return b.toUtf8();
                }
            }
            return b.isEmpty() ? null : b.toUtf8();
        }

        private void drainRemaining() throws IOException {
            int r;
            while ((r = in.read()) >= 0) {
                if (r == '\n' || r == '\r') {
                    lastWasCr = (r == '\r');
                    return;
                }
            }
        }

        /** Auto-growing but capped byte buffer. */
        private static final class ByteArrayBuilder {
            private byte[] buf;
            int len;
            private final int cap;

            ByteArrayBuilder(int cap) {
                this.cap = cap;
                this.buf = new byte[Math.min(cap, 128)];
            }

            boolean append(byte b) {
                if (len >= cap)
                    return false;
                if (len == buf.length) {
                    int next = Math.min(cap, buf.length * 2);
                    byte[] grown = new byte[next];
                    System.arraycopy(buf, 0, grown, 0, len);
                    buf = grown;
                }
                buf[len++] = b;
                return true;
            }

            boolean isEmpty() {
                return len == 0;
            }

            String toUtf8() {
                return new String(buf, 0, len, StandardCharsets.UTF_8);
            }
        }
    }
}
