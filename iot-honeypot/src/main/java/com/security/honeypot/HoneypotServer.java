package com.security.honeypot;

import org.apache.sshd.common.cipher.BuiltinCiphers;
import org.apache.sshd.common.signature.BuiltinSignatures;
import org.apache.sshd.common.keyprovider.KeyPairProvider;
import org.apache.sshd.common.session.Session;
import org.apache.sshd.common.session.SessionListener;
import org.apache.sshd.server.SshServer;
import org.apache.sshd.server.session.ServerSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.IOException;
import java.security.Security;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.sshd.common.compression.BuiltinCompressions;

/*
 * BouncyCastle is shipped as an external JAR under ./lib (see pom.xml) so its
 * signed manifest stays intact — JDK 23 rejects repackaged provider JARs with
 * `JCE cannot authenticate the provider BC`. Apache MINA SSHD 2.12.0's
 * `AbstractSignatureFactory` hard-codes `Signature.getInstance("Ed25519", "BC")`
 * for Ed25519 signing, so without BC the host-key path dies with
 * `EdDSA Signer not available`.
 */
import org.bouncycastle.jce.provider.BouncyCastleProvider;

/**
 * HoneypotServer
 *
 * Entry point. Boots the embedded SQLite store, then starts the
 * services selected by -Dhoneypot.profile:
 *
 * 1) SSH on port 2222 (catches legacy IoT scanners and operators).
 * 2) HTTP web admin on port 8080 (catches routers, cameras, locks).
 * 3) RTSP stub on port 554 (catches IP-camera scanners).
 *
 * Every service uses the same bait posture: accept any credentials,
 * record every event, never actually execute attacker input.
 */
public final class HoneypotServer {

    private static final Logger LOG = LoggerFactory.getLogger(HoneypotServer.class);

    /**
     * Defensive getter: empty / null system property falls back to default.
     * Used for the static final tunables below so an empty -D does not
     * crash the JVM during class initialization.
     */
    private static String sysOrDefault(String key, String fallback) {
        String v = System.getProperty(key);
        return (v == null || v.isBlank()) ? fallback : v;
    }

    private static int sysIntOrDefault(String key, int fallback) {
        String v = sysOrDefault(key, null);
        if (v == null)
            return fallback;
        try {
            return Integer.parseInt(v.trim());
        } catch (NumberFormatException e) {
            return fallback;
        }
    }

    private static long sysLongOrDefault(String key, long fallback) {
        String v = sysOrDefault(key, null);
        if (v == null)
            return fallback;
        try {
            return Long.parseLong(v.trim());
        } catch (NumberFormatException e) {
            return fallback;
        }
    }

    /** Port the honeypot listens on. Defaults to 2222 (non-privileged). */
    private static final int LISTEN_PORT = sysIntOrDefault("honeypot.port", 2222);

    /** Optional bind address; empty string = all interfaces. */
    private static final String BIND_ADDRESS = sysOrDefault("honeypot.bind", "0.0.0.0");

    /** Persistent host key file; auto-created on first run. */
    private static final String HOST_KEY_PATH = "hostkey.ser";

    /** HTTP port for web-admin profile. */
    private static final int HTTP_PORT = sysIntOrDefault("honeypot.http.port", 8080);

    /** RTSP port for camera profiles. */
    private static final int RTSP_PORT = sysIntOrDefault("honeypot.rtsp.port", 554);

    // ------------------------------------------------------------------
    // Resource-limit tunables (DoS hardening, audit 2026-07-28).
    // Exposed as -Dhoneypot.<key>=<value> so operators can tune without
    // recompiling. The defaults below were chosen for a single honeypot
    // instance on a modest x86 host (≤ 50 global SSH sessions,
    // ≤ 3 per IP, idle disconnect after 30s).
    // ------------------------------------------------------------------

    /** Idle disconnect — any session silent for this long is forcibly closed. */
    private static final long SSH_IDLE_TIMEOUT_MS = sysLongOrDefault("honeypot.ssh.idleTimeoutMs", 30000L);

    /** Hard cap on simultaneous SSH sessions, global. */
    private static final int SSH_MAX_SESSIONS = sysIntOrDefault("honeypot.ssh.maxSessions", 50);

    /** Hard cap on simultaneous SSH sessions per remote IP. */
    private static final int SSH_MAX_SESSIONS_PER_IP = sysIntOrDefault("honeypot.ssh.maxPerIp", 3);

    /** Max bytes the NIO read-buffer will hold before back-pressuring. */
    private static final int SSH_READ_BUFFER_SIZE = sysIntOrDefault("honeypot.ssh.readBuffer", 262144); // 256 KiB

    /** Max bytes the NIO write-buffer will hold. */
    private static final int SSH_WRITE_BUFFER_SIZE = sysIntOrDefault("honeypot.ssh.writeBuffer", 131072); // 128 KiB

    /** Soft cap on how much cipher-decoded data we'll buffer per session. */
    private static final int SSH_WINDOW_SIZE = sysIntOrDefault("honeypot.ssh.windowSize", 2097152); // 2 MiB

    /** Active-session counters for the global + per-IP limiters. */
    private static final AtomicInteger ACTIVE_SESSIONS = new AtomicInteger();
    private static final Map<String, AtomicInteger> PER_IP_COUNTS = new ConcurrentHashMap<>();

    public static void main(String[] args) {
        try {
            // 1) Database first so every event from boot onward is durable.
            DatabaseManager.initialize();
        } catch (Exception e) {
            LOG.error("Database initialization failed; refusing to start.", e);
            System.exit(1);
        }

        DeviceProfile profile = DeviceProfile.parse(System.getProperty("honeypot.profile"));
        LOG.info("Profile: {}", profile);
        for (String svc : profile.services) {
            switch (svc) {
                case "ssh" -> startSsh();
                case "http" -> startHttp(profile);
                case "rtsp" -> startRtsp();
                default -> LOG.warn("Unknown service: {}", svc);
            }
        }

        // Block forever; shutdown hook stops everything.
        Object lock = new Object();
        synchronized (lock) {
            try {
                lock.wait();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    private static void startSsh() {
        SshServer server = SshServer.setUpDefaultServer();
        server.setPort(LISTEN_PORT);
        server.setHost(BIND_ADDRESS);

        // ----------------------------------------------------------------
        // Rule 4 + 5: Bounded NIO buffers. MINA exposes these as typed
        // Property constants on AbstractSession / ServerSessionImpl. We
        // cap the read/write packet buffers and the per-session window so
        // a misbehaving client cannot push the JVM into swapping.
        // ----------------------------------------------------------------
        // ------------------------------------------------------------------
        // Rule 4 + 5: Bounded NIO buffers. In sshd-core 2.12.0 the
        // factory manager exposes a plain Map<String, Object> via
        // getProperties(); the typed Property<>-keyed setters were
        // introduced in 2.13+. So we put the raw string keys directly.
        // The keys are the canonical SSHD names documented in
        // AbstractFactoryManager / AbstractSession.
        // ------------------------------------------------------------------
        Map<String, Object> props = server.getProperties();
        props.put("read-buffer-size", SSH_READ_BUFFER_SIZE);
        props.put("write-buffer-size", SSH_WRITE_BUFFER_SIZE);
        props.put("window-size", SSH_WINDOW_SIZE);
        props.put("packet-buffer-size", SSH_READ_BUFFER_SIZE);
        props.put("max-packet-size", SSH_READ_BUFFER_SIZE);
        // Disable any cipher modes that would inflate the in-flight buffer
        // (compression is a classic amplifier for IoT-bots).
        server.setCipherFactories(
                java.util.List.of(BuiltinCiphers.aes256ctr, BuiltinCiphers.aes128ctr));
        server.setCompressionFactories(
                java.util.List.of(BuiltinCompressions.none));

        // ----------------------------------------------------------------
        // Rule 1: Idle disconnect. Apache MINA's default is "no timeout",
        // which lets abandoned sessions accumulate. We set the
        // idle-timeout property on the factory manager's properties map.
        // ----------------------------------------------------------------
        props.put("idle-timeout", SSH_IDLE_TIMEOUT_MS);

        // ----------------------------------------------------------------
        // Rule 2 + 3: Connection throttling via a SessionListener.
        // The listener runs synchronously on the I/O selector thread, so
        // decrements are race-free; the per-IP map uses
        // ConcurrentHashMap so we never block long.
        // ----------------------------------------------------------------
        final SessionListener sessionLimiter = new SessionListener() {
            @Override
            public void sessionCreated(Session s) {
                ServerSession ss = (ServerSession) s;
                String ip = remoteIp(ss);
                int global = ACTIVE_SESSIONS.incrementAndGet();
                if (global > SSH_MAX_SESSIONS) {
                    ACTIVE_SESSIONS.decrementAndGet();
                    LOG.warn("SSH session refused (global cap {} reached): {}",
                            SSH_MAX_SESSIONS, ip);
                    ss.close(false); // 0 = not graceful, drop immediately
                    return;
                }
                AtomicInteger perIp = PER_IP_COUNTS.computeIfAbsent(
                        ip, k -> new AtomicInteger());
                int ipCount = perIp.incrementAndGet();
                if (ipCount > SSH_MAX_SESSIONS_PER_IP) {
                    perIp.decrementAndGet();
                    ACTIVE_SESSIONS.decrementAndGet();
                    LOG.warn("SSH session refused (per-IP cap {} reached): {}",
                            SSH_MAX_SESSIONS_PER_IP, ip);
                    ss.close(false);
                    return;
                }
                LOG.debug("SSH session opened from {} (global={}/{}, perIp={}/{})",
                        ip, global, SSH_MAX_SESSIONS, ipCount, SSH_MAX_SESSIONS_PER_IP);
            }

            @Override
            public void sessionClosed(Session s) {
                ServerSession ss = (ServerSession) s;
                String ip = remoteIp(ss);
                ACTIVE_SESSIONS.decrementAndGet();
                AtomicInteger perIp = PER_IP_COUNTS.get(ip);
                if (perIp != null) {
                    int left = perIp.decrementAndGet();
                    if (left <= 0)
                        PER_IP_COUNTS.remove(ip, perIp);
                }
                // Explicit Rule 5 cleanup: drop the session object so its
                // channel registry, executor tasks, and NIO buffers are
                // released immediately rather than waiting for GC.
                ss.close(true);
            }

            // The remaining SessionListener events are not relevant to the
            // limiter; the defaults are no-ops.
            @Override
            public void sessionEvent(Session s, Event e) {
                /* nop */ }

            @Override
            public void sessionException(Session s, Throwable t) {
                if (t != null) {
                    // Rule 5: log only the exception type, never the message,
                    // so a misbehaving client cannot poison the operator log.
                    LOG.debug("SSH session exception (type={})",
                            t.getClass().getSimpleName());
                }
            }
        };
        server.addSessionListener(sessionLimiter);

        // Host key. We use RSA instead of Ed25519 because MINA SSHD 2.12.0 has
        // known classpath issues with BouncyCastle's EdDSA signer (it throws
        // "EdDSA Signer not available"). RSA is also much more realistic for an
        // old IoT device (our honeypot profile).
        try {
            org.apache.sshd.server.keyprovider.SimpleGeneratorHostKeyProvider keyProvider =
                new org.apache.sshd.server.keyprovider.SimpleGeneratorHostKeyProvider(Path.of(HOST_KEY_PATH));
            keyProvider.setAlgorithm("RSA");
            keyProvider.setKeySize(2048);
            server.setKeyPairProvider(keyProvider);
        } catch (Exception e) {
            LOG.error("Failed to configure host key provider.", e);
            System.exit(1);
        }

        // Publish modern signature algorithms (for RSA).
        server.setSignatureFactories(java.util.List.of(
                BuiltinSignatures.rsaSHA512,
                BuiltinSignatures.rsaSHA256,
                BuiltinSignatures.rsa));

        // CRITICAL SECURITY LOGIC:
        // Always return true. The honeypot's job is to *let attackers in*
        // so we can observe them. Real authentication would defeat the
        // purpose. Every attempt is logged with the attacker-supplied
        // credentials for forensic and threat-intel value.
        server.setPasswordAuthenticator((username, password, session) -> {
            String ip = remoteIp(session);
            String pw = password == null ? "" : password;
            LOG.info("AUTH ATTEMPT ip={} user='{}' pass='{}'", ip, username, pw);
            DatabaseManager.logAuth(ip, username, pw);
            return true;
        });

        // Same bait posture for keyboard-interactive (used by many IoT bots).
        // KeyboardInteractiveAuthenticator in 2.12.0 declares two abstract
        // methods (generateChallenge + authenticate), so it cannot be a
        // lambda — we use an anonymous class instead.
        server.setKeyboardInteractiveAuthenticator(
                new org.apache.sshd.server.auth.keyboard.KeyboardInteractiveAuthenticator() {
                    @Override
                    public org.apache.sshd.server.auth.keyboard.InteractiveChallenge generateChallenge(
                            org.apache.sshd.server.session.ServerSession session,
                            String username, String lang, String subMethods)
                            throws Exception {
                        // No interactive challenge is needed — we accept
                        // everything the attacker types, so the response
                        // to the challenge is an empty prompt list.
                        return new org.apache.sshd.server.auth.keyboard.InteractiveChallenge() {
                            @Override
                            public String getInteractionName() {
                                return "";
                            }

                            @Override
                            public String getInteractionInstruction() {
                                return "";
                            }

                            @Override
                            public String getLanguageTag() {
                                return "en";
                            }

                            @Override
                            public java.util.List<org.apache.sshd.server.auth.keyboard.PromptEntry> getPrompts() {
                                return java.util.Collections.emptyList();
                            }
                        };
                    }

                    @Override
                    public boolean authenticate(org.apache.sshd.server.session.ServerSession session,
                            String username,
                            java.util.List<String> responses)
                            throws Exception {
                        String ip = remoteIp(session);
                        LOG.info("KEYBOARD-INTERACTIVE ATTEMPT ip={} user='{}'", ip, username);
                        DatabaseManager.logAuth(ip, username, String.join(",", responses));
                        return true;
                    }
                });

        // Wire the fake shell.
        server.setShellFactory(new FakeShellFactory());

        // The shutdown hook is a single static block below this method — it
        // stops every service registered via SERVICES.add(...).
        try {
            server.start();
            SERVICES.add(() -> {
                try {
                    server.stop();
                } catch (Exception e) {
                    /* ignore */ }
            });
            LOG.info("SSH honeypot listening on {}:{} "
                    + "(idle={}ms, max={}, perIp={}, readBuf={}, writeBuf={})",
                    BIND_ADDRESS, LISTEN_PORT,
                    SSH_IDLE_TIMEOUT_MS, SSH_MAX_SESSIONS,
                    SSH_MAX_SESSIONS_PER_IP, SSH_READ_BUFFER_SIZE, SSH_WRITE_BUFFER_SIZE);
        } catch (Exception e) {
            LOG.error("Failed to start SSH server.", e);
            System.exit(1);
        }
    }

    private static void startHttp(DeviceProfile profile) {
        try {
            HttpHoneypot http = new HttpHoneypot(HTTP_PORT, BIND_ADDRESS, profile);
            http.start();
            SERVICES.add(http::stop);
            LOG.info("HTTP honeypot listening on {}:{} ({})", BIND_ADDRESS, HTTP_PORT, profile);
        } catch (Exception e) {
            LOG.error("Failed to start HTTP honeypot.", e);
            System.exit(1);
        }
    }

    private static void startRtsp() {
        try {
            RtspStub rtsp = new RtspStub(RTSP_PORT, BIND_ADDRESS);
            rtsp.start();
            SERVICES.add(rtsp::stop);
            LOG.info("RTSP stub listening on {}:{}", BIND_ADDRESS, RTSP_PORT);
        } catch (Exception e) {
            LOG.error("Failed to start RTSP stub.", e);
            System.exit(1);
        }
    }

    /** Live service registry — used by the shutdown hook. */
    private static final List<Runnable> SERVICES = java.util.Collections.synchronizedList(new ArrayList<>());

    /** Static initializer for the shutdown hook. */
    static {
        if (Security.getProvider(BouncyCastleProvider.PROVIDER_NAME) == null) {
            Security.insertProviderAt(new BouncyCastleProvider(), 1);
            LOG.info("Registered BouncyCastleProvider at position 1 "
                    + "(required for MINA SSHD Ed25519 host key signing and EdDSA session auth).");
        } else {
            LOG.debug("BouncyCastleProvider already registered.");
        }

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            LOG.info("Shutdown signal received; stopping honeypot...");
            synchronized (SERVICES) {
                for (Runnable stop : SERVICES) {
                    try {
                        stop.run();
                    } catch (Exception ignored) {
                        /* shutting down */ }
                }
            }
        }, "honeypot-shutdown"));
    }

    /**
     * Resolve the remote address for the active session. Falls back to
     * "unknown" rather than throwing; we never want logging to crash
     * the SSH layer.
     */
    private static String remoteIp(ServerSession session) {
        try {
            if (session.getRemoteAddress() instanceof InetSocketAddress addr) {
                return addr.getAddress().getHostAddress();
            }
            return String.valueOf(session.getRemoteAddress());
        } catch (Exception e) {
            return "unknown";
        }
    }

    /**
     * Generate (or reuse) a stable Ed25519 host keypair for the SSH server.
     *
     * We can't delegate to {@code SimpleGeneratorHostKeyProvider} because its
     * built-in generator calls {@code KeyPairGenerator.getInstance("ssh-ed25519")},
     * a non-standard JCE alias that BC doesn't expose. Going through the
     * standard JCE API (algorithm = "Ed25519") works on JDK 15+ and on BC 1.70+.
     *
     * The key is serialized with Java's standard PKCS#8 encoding so future
     * restarts reuse the same identity (the file is overwritten in MINA's
     * native format on first run after we hand it the keypair).
     */
    private static java.security.KeyPair loadOrCreateEd25519KeyPair(Path keyPath) throws Exception {
        java.security.KeyPair kp;
        if (Files.exists(keyPath) && Files.size(keyPath) > 0) {
            // Try PKCS#8 first (our format). If MINA rewrote the file in
            // its native format on a prior run, fall back to native parsing.
            try (java.io.InputStream in = Files.newInputStream(keyPath)) {
                byte[] encoded = in.readAllBytes();
                java.security.spec.PKCS8EncodedKeySpec privSpec = new java.security.spec.PKCS8EncodedKeySpec(encoded);
                java.security.KeyFactory kf = java.security.KeyFactory.getInstance("Ed25519");
                java.security.PrivateKey priv = kf.generatePrivate(privSpec);
                // Public key has to be derived from the private key (Ed25519).
                java.security.spec.NamedParameterSpec paramSpec = new java.security.spec.NamedParameterSpec("Ed25519");
                byte[] pubEncoded = deriveEd25519Public(priv);
                java.security.spec.X509EncodedKeySpec pubSpec = new java.security.spec.X509EncodedKeySpec(pubEncoded);
                java.security.PublicKey pub = kf.generatePublic(pubSpec);
                kp = new java.security.KeyPair(pub, priv);
                LOG.info("Loaded existing Ed25519 host key from {}", keyPath);
                return kp;
            } catch (Exception ignored) {
                // Not in our format; fall through to regenerate. Stale keys
                // (e.g. the old ssh-rsa hostkey.ser) will be overwritten.
            }
        }
        java.security.KeyPairGenerator g = java.security.KeyPairGenerator.getInstance("Ed25519");
        kp = g.generateKeyPair();
        // Persist in PKCS#8 so we can reload next start.
        byte[] priv = kp.getPrivate().getEncoded();
        Files.createDirectories(keyPath.getParent() == null
                ? Path.of(".")
                : keyPath.getParent());
        Files.write(keyPath, priv);
        LOG.info("Generated new Ed25519 host key, written to {}", keyPath);
        return kp;
    }

    /**
     * Derive the X.509-encoded Ed25519 public key bytes from a private key.
     * JDK 15+ doesn't expose a direct "getPublic()" on EdDSA private keys,
     * so we use reflection-free KeyFactory tricks: extract the raw point
     * from the BC private key if available, otherwise fall back to calling
     * the provider's key agreement via the public reference on the pair.
     */
    private static byte[] deriveEd25519Public(java.security.PrivateKey priv)
            throws java.security.spec.InvalidKeySpecException,
            java.security.NoSuchAlgorithmException {
        // JCA EdDSA private keys in BC expose getPublic() via Ed25519PrivateKey
        // but the JCE interface doesn't, so we go through reflection once.
        try {
            java.security.PublicKey pub = (java.security.PublicKey) priv.getClass()
                    .getMethod("getPublicKey").invoke(priv);
            return pub.getEncoded();
        } catch (ReflectiveOperationException ignored) {
            // Last resort: generate a fresh pair (caller should regenerate).
            throw new java.security.spec.InvalidKeySpecException(
                    "Cannot derive Ed25519 public key from private key of class "
                            + priv.getClass().getName());
        }
    }
}