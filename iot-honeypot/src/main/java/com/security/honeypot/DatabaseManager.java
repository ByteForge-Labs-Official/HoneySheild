package com.security.honeypot;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * DatabaseManager
 *
 * Owns the embedded SQLite lifecycle (honeypot.db). Exposes
 * parameterized helpers so the rest of the honeypot never builds
 * SQL with string concatenation, which would be both a real risk
 * and a credibility hit if an attacker ever pivoted.
 */
public final class DatabaseManager {

    private static final Logger LOG = LoggerFactory.getLogger(DatabaseManager.class);

    /** JDBC URL for an embedded SQLite file in the working directory. */
    private static final String DB_URL = "jdbc:sqlite:honeypot.db";

    /** DDL: capture every brute-force attempt. */
    private static final String CREATE_AUTH_LOGS =
            "CREATE TABLE IF NOT EXISTS auth_logs ("
                    + " id          INTEGER PRIMARY KEY AUTOINCREMENT,"
                    + " timestamp   TEXT    NOT NULL,"
                    + " ip_address  TEXT    NOT NULL,"
                    + " username    TEXT    NOT NULL,"
                    + " password    TEXT    NOT NULL,"
                    + " protocol    TEXT    NOT NULL DEFAULT 'ssh'"
                    + ");";

    /** DDL: capture every shell command the attacker types. */
    private static final String CREATE_COMMAND_LOGS =
            "CREATE TABLE IF NOT EXISTS command_logs ("
                    + " id          INTEGER PRIMARY KEY AUTOINCREMENT,"
                    + " timestamp   TEXT    NOT NULL,"
                    + " ip_address  TEXT    NOT NULL,"
                    + " command     TEXT    NOT NULL,"
                    + " protocol    TEXT    NOT NULL DEFAULT 'ssh'"
                    + ");";

    /** DDL: capture every HTTP request hitting the web-admin honeypot. */
    private static final String CREATE_HTTP_LOGS =
            "CREATE TABLE IF NOT EXISTS http_request_logs ("
                    + " id          INTEGER PRIMARY KEY AUTOINCREMENT,"
                    + " timestamp   TEXT    NOT NULL,"
                    + " ip_address  TEXT    NOT NULL,"
                    + " method      TEXT    NOT NULL,"
                    + " path        TEXT    NOT NULL,"
                    + " user_agent  TEXT,"
                    + " username    TEXT,"
                    + " password    TEXT,"
                    + " status      INTEGER NOT NULL"
                    + ");";

    /** Parameterized insert for auth attempts. */
    private static final String INSERT_AUTH =
            "INSERT INTO auth_logs (timestamp, ip_address, username, password, protocol) "
                    + "VALUES (?, ?, ?, ?, ?);";

    /** Parameterized insert for shell commands. */
    private static final String INSERT_COMMAND =
            "INSERT INTO command_logs (timestamp, ip_address, command, protocol) "
                    + "VALUES (?, ?, ?, ?);";

    /** Parameterized insert for HTTP requests. */
    private static final String INSERT_HTTP =
            "INSERT INTO http_request_logs "
                    + "(timestamp, ip_address, method, path, user_agent, username, password, status) "
                    + "VALUES (?, ?, ?, ?, ?, ?, ?, ?);";

    private DatabaseManager() {
        // utility class
    }

    /**
     * Initialize SQLite, ensure the schema exists, and force a
     * write-ahead-log pragma that plays nicely with WAL under
     * concurrent shell sessions.
     */
    public static void initialize() throws SQLException {
        try (Connection conn = DriverManager.getConnection(DB_URL);
             Statement stmt = conn.createStatement()) {

            // WAL is more concurrent and crash-resilient than the rollback journal.
            try {
                stmt.execute("PRAGMA journal_mode=WAL;");
            } catch (SQLException pragma) {
                LOG.warn("Could not enable WAL mode: {}", pragma.getMessage());
            }

            stmt.execute(CREATE_AUTH_LOGS);
            stmt.execute(CREATE_COMMAND_LOGS);
            stmt.execute(CREATE_HTTP_LOGS);

            // Backward-compat: existing DBs may not have the protocol columns.
            addColumnIfMissing(conn, "auth_logs",    "protocol", "TEXT NOT NULL DEFAULT 'ssh'");
            addColumnIfMissing(conn, "command_logs", "protocol", "TEXT NOT NULL DEFAULT 'ssh'");

            LOG.info("Database initialized at {}", DB_URL);
        }
    }

    /**
     * SQLite has no ADD COLUMN IF NOT EXISTS; this emulates it.
     *
     * <p><b>Security note (Rule 3):</b> SQLite does not allow bind
     * parameters in DDL (table or column names cannot be placeholders).
     * This method is therefore the one exception in the codebase that
     * concatenates identifiers into a SQL string. It is safe because
     * both {@code table} and {@code column} are hard-coded constants
     * (see the two callers in {@link #initialize()}) — no attacker
     * input ever reaches here. If you ever change the call sites to
     * accept dynamic identifiers, switch to a strict whitelist.
     */
    private static void addColumnIfMissing(Connection conn, String table,
                                           String column, String definition) throws SQLException {
        String check = "PRAGMA table_info(" + table + ")";
        try (Statement s = conn.createStatement();
             java.sql.ResultSet rs = s.executeQuery(check)) {
            while (rs.next()) {
                if (column.equalsIgnoreCase(rs.getString("name"))) {
                    return;
                }
            }
        }
        try (Statement s = conn.createStatement()) {
            s.executeUpdate("ALTER TABLE " + table + " ADD COLUMN "
                    + column + " " + definition);
            LOG.info("Added missing column {}.{}", table, column);
        }
    }

    /**
     * Persist a credential attempt. Uses bind variables, never
     * concatenates attacker-supplied strings into SQL.
     */
    public static void logAuth(String ipAddress, String username, String password) {
        logAuth(ipAddress, username, password, "ssh");
    }

    /** Auth attempt with explicit protocol tag ("ssh", "http", "rtsp"). */
    public static void logAuth(String ipAddress, String username, String password,
                               String protocol) {
        String ts = nowIso();
        try (Connection conn = DriverManager.getConnection(DB_URL);
             PreparedStatement ps = conn.prepareStatement(INSERT_AUTH)) {

            ps.setString(1, ts);
            ps.setString(2, sanitize(ipAddress, 64));
            ps.setString(3, sanitize(username, 128));
            ps.setString(4, sanitize(password, 256));
            ps.setString(5, sanitize(protocol, 16));
            ps.executeUpdate();

        } catch (SQLException e) {
            LOG.error("Failed to log auth attempt from {}: {}", ipAddress, e.getMessage());
        }
    }

    /**
     * Persist a single shell command issued by the attacker.
     */
    public static void logCommand(String ipAddress, String command) {
        logCommand(ipAddress, command, "ssh");
    }

    /** Command with explicit protocol tag. */
    public static void logCommand(String ipAddress, String command, String protocol) {
        String ts = nowIso();
        try (Connection conn = DriverManager.getConnection(DB_URL);
             PreparedStatement ps = conn.prepareStatement(INSERT_COMMAND)) {

            ps.setString(1, ts);
            ps.setString(2, sanitize(ipAddress, 64));
            ps.setString(3, sanitize(command, 4096));
            ps.setString(4, sanitize(protocol, 16));
            ps.executeUpdate();

        } catch (SQLException e) {
            LOG.error("Failed to log command from {}: {}", ipAddress, e.getMessage());
        }
    }

    /** Persist a single HTTP request (and optionally the credentials it carried). */
    public static void logHttpRequest(String ipAddress, String method, String path,
                                      String userAgent, String username, String password,
                                      int status) {
        String ts = nowIso();
        try (Connection conn = DriverManager.getConnection(DB_URL);
             PreparedStatement ps = conn.prepareStatement(INSERT_HTTP)) {

            ps.setString(1, ts);
            ps.setString(2, sanitize(ipAddress, 64));
            ps.setString(3, sanitize(method, 8));
            ps.setString(4, sanitize(path, 512));
            ps.setString(5, sanitize(userAgent, 512));
            ps.setString(6, sanitize(username, 128));
            ps.setString(7, sanitize(password, 256));
            ps.setInt(8, status);
            ps.executeUpdate();

        } catch (SQLException e) {
            LOG.error("Failed to log HTTP request from {}: {}", ipAddress, e.getMessage());
        }
    }

    /** ISO-8601 UTC timestamp; SQLite-friendly TEXT. */
    private static String nowIso() {
        return java.time.OffsetDateTime
                .now(java.time.ZoneOffset.UTC)
                .format(java.time.format.DateTimeFormatter.ISO_OFFSET_DATE_TIME);
    }

    /**
     * Trim, clamp, and scrub attacker-controlled strings before they
     * hit the database. Bind parameters are the *primary* defense
     * against SQL injection; this is defensive hardening — strip
     * ANSI escapes, control chars, and null bytes so SQLite never
     * has to deal with poisoned bytes (Rule 2 + Rule 3 belt-and-braces).
     */
    private static String sanitize(String value, int maxLen) {
        if (value == null) {
            return "";
        }
        String scrubbed = Sanitizer.cleanValue(value);
        if (scrubbed.length() > maxLen) {
            scrubbed = scrubbed.substring(0, maxLen);
        }
        return scrubbed;
    }
}
