package com.security.honeypot;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

/**
 * HoneypotCli
 *
 * Friendly operator-facing commands that don't require knowing SQL or
 * installing sqlite3. Everything is backed by the same honeypot.db the
 * server writes to.
 *
 * java -jar iot-honeypot.jar --stats
 * java -jar iot-honeypot.jar --logs 20
 * java -jar iot-honeypot.jar --commands 50
 * java -jar iot-honeypot.jar --export logs.csv
 * java -jar iot-honeypot.jar --reset --yes
 * java -jar iot-honeypot.jar --menu
 */
public final class HoneypotCli {

    private static final String DB_URL = "jdbc:sqlite:honeypot.db";
    private static final DateTimeFormatter TS_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss z");

    static {
        ensureBouncyCastle();
    }

    public static void ensureBouncyCastle() {
        if (java.security.Security
                .getProvider(org.bouncycastle.jce.provider.BouncyCastleProvider.PROVIDER_NAME) == null) {
            java.security.Security.insertProviderAt(new org.bouncycastle.jce.provider.BouncyCastleProvider(), 1);
        }
    }

    private HoneypotCli() {
        /* entry point only */ }

    public static void main(String[] args) throws Exception {
        ensureBouncyCastle();
        if (args.length == 0) {
            // No subcommand: behave like the server.
            HoneypotServer.main(new String[] {});
            return;
        }

        String cmd = args[0];
        switch (cmd) {
            case "--stats", "stats" -> printStats();
            case "--logs", "logs" -> tailAuthLogs(argInt(args, 1, 20));
            case "--commands", "commands" -> tailCommandLogs(argInt(args, 1, 20));
            case "--requests", "http" -> tailHttpRequests(argInt(args, 1, 20));
            case "--top-users" -> topAttemptedUsers(argInt(args, 1, 10));
            case "--top-ips" -> topSourceIps(argInt(args, 1, 10));
            case "--watch" -> watch();
            case "--export" -> {
                String out = args.length < 2 ? "honeypot-export.csv" : args[1];
                String table = args.length < 3 ? "all" : args[2].toLowerCase();
                exportCsv(out, table);
            }
            case "--reset" -> reset(confirmFlag(args));
            case "--serve", "serve" -> HoneypotServer.main(new String[] {});
            case "--profile", "as" -> serveAsProfile(args);
            case "--menu", "-i", "menu" -> interactiveMenu();
            case "--help", "-h", "help" -> printHelp();
            default -> {
                System.err.println("Unknown command: " + cmd);
                printHelp();
                System.exit(2);
            }
        }
    }

    /** "as camera" / "as doorlock" / "as router" — start with a profile. */
    private static void serveAsProfile(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: --profile <camera|router|doorlock|website|ssh|multi>");
            System.exit(2);
        }
        // Pass the profile through the system property used by HoneypotServer.
        System.setProperty("honeypot.profile", args[1].toUpperCase(java.util.Locale.ROOT));
        HoneypotServer.main(new String[] {});
    }

    // ---------------- Commands ----------------

    private static void printStats() throws SQLException {
        System.out.println("== Honeypot Stats ==");
        try (Connection c = DriverManager.getConnection(DB_URL);
                Statement s = c.createStatement()) {
            row("auth attempts", s, "SELECT COUNT(*) FROM auth_logs");
            row("unique IPs", s, "SELECT COUNT(DISTINCT ip_address) FROM auth_logs");
            row("commands", s, "SELECT COUNT(*) FROM command_logs");
            row("http requests", s, "SELECT COUNT(*) FROM http_request_logs");
            row("first seen", s, "SELECT MIN(timestamp) FROM auth_logs", "n/a");
            row("last attempt", s, "SELECT MAX(timestamp) FROM auth_logs", "n/a");
            row("last command", s, "SELECT MAX(timestamp) FROM command_logs", "n/a");
            row("last http req", s, "SELECT MAX(timestamp) FROM http_request_logs", "n/a");
        }
    }

    private static void tailHttpRequests(int limit) throws SQLException {
        String sql = "SELECT id, timestamp, ip_address, method, path, status, "
                + "COALESCE(username,'') AS user, COALESCE(password,'') AS pass "
                + "FROM http_request_logs ORDER BY id DESC LIMIT ?";
        System.out.println("== Last " + limit + " HTTP requests ==");
        try (Connection c = DriverManager.getConnection(DB_URL);
                PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setInt(1, limit);
            try (ResultSet rs = ps.executeQuery()) {
                printTable(rs, List.of("#", "timestamp", "ip", "method", "path",
                        "status", "user", "password"));
            }
        }
    }

    private static void tailAuthLogs(int limit) throws SQLException {
        String sql = "SELECT id, timestamp, ip_address, username, password "
                + "FROM auth_logs ORDER BY id DESC LIMIT ?";
        System.out.println("== Last " + limit + " auth attempts ==");
        try (Connection c = DriverManager.getConnection(DB_URL);
                PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setInt(1, limit);
            try (ResultSet rs = ps.executeQuery()) {
                printTable(rs, List.of("#", "timestamp", "ip", "user", "password"));
            }
        }
    }

    private static void tailCommandLogs(int limit) throws SQLException {
        String sql = "SELECT id, timestamp, ip_address, command "
                + "FROM command_logs ORDER BY id DESC LIMIT ?";
        System.out.println("== Last " + limit + " shell commands ==");
        try (Connection c = DriverManager.getConnection(DB_URL);
                PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setInt(1, limit);
            try (ResultSet rs = ps.executeQuery()) {
                printTable(rs, List.of("#", "timestamp", "ip", "command"));
            }
        }
    }

    private static void topAttemptedUsers(int limit) throws SQLException {
        String sql = "SELECT username, COUNT(*) AS hits FROM auth_logs "
                + "GROUP BY username ORDER BY hits DESC LIMIT ?";
        System.out.println("== Top " + limit + " usernames ==");
        try (Connection c = DriverManager.getConnection(DB_URL);
                PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setInt(1, limit);
            try (ResultSet rs = ps.executeQuery()) {
                printTable(rs, List.of("username", "hits"));
            }
        }
    }

    private static void topSourceIps(int limit) throws SQLException {
        String sql = "SELECT ip_address, COUNT(*) AS hits FROM auth_logs "
                + "GROUP BY ip_address ORDER BY hits DESC LIMIT ?";
        System.out.println("== Top " + limit + " source IPs ==");
        try (Connection c = DriverManager.getConnection(DB_URL);
                PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setInt(1, limit);
            try (ResultSet rs = ps.executeQuery()) {
                printTable(rs, List.of("ip", "hits"));
            }
        }
    }

    private static void watch() {
        System.out.println("Watching honeypot.db every 5s. Ctrl+C to stop.");
        Runnable tick = () -> {
            try {
                printStats();
            } catch (SQLException e) {
                System.err.println("DB error: " + e.getMessage());
            }
            System.out.println("---");
        };
        try {
            while (true) {
                tick.run();
                Thread.sleep(5_000);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    /**
     * Whitelist of exportable tables. Rule 3: SQL identifiers can't be
     * bound, so we explicitly enumerate the only legal values instead
     * of concatenating operator input.
     */
    private static final Map<String, List<String>> EXPORT_TABLES = Map.of(
            "all", List.of("auth_logs", "command_logs", "http_request_logs"),
            "auth", List.of("auth_logs"),
            "auth_logs", List.of("auth_logs"),
            "commands", List.of("command_logs"),
            "command_logs", List.of("command_logs"),
            "http", List.of("http_request_logs"),
            "http_request_logs", List.of("http_request_logs"));

    private static void exportCsv(String outPath, String table) throws SQLException, IOException {
        // Whitelist lookup — never trust the operator-supplied token to
        // appear in the SQL string itself.
        List<String> tables = EXPORT_TABLES.get(table);
        if (tables == null) {
            System.err.println("Unknown export target: " + table);
            System.exit(2);
            return;
        }

        Path out = Path.of(outPath);
        try (var writer = Files.newBufferedWriter(out, StandardCharsets.UTF_8,
                StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING)) {
            try (Connection c = DriverManager.getConnection(DB_URL)) {
                for (String t : tables) {
                    writer.write("# table=" + t);
                    writer.newLine();
                    try (Statement s = c.createStatement();
                            ResultSet rs = s.executeQuery("SELECT * FROM " + t)) {
                        ResultSetMetaData md = rs.getMetaData();
                        int cols = md.getColumnCount();
                        StringBuilder header = new StringBuilder();
                        for (int i = 1; i <= cols; i++) {
                            if (i > 1)
                                header.append(',');
                            header.append(csv(md.getColumnLabel(i)));
                        }
                        writer.write(header.toString());
                        writer.newLine();
                        while (rs.next()) {
                            StringBuilder row = new StringBuilder();
                            for (int i = 1; i <= cols; i++) {
                                if (i > 1)
                                    row.append(',');
                                row.append(csv(rs.getString(i)));
                            }
                            writer.write(row.toString());
                            writer.newLine();
                        }
                    }
                    writer.newLine();
                }
            }
        }
        System.out.println("Exported to " + out.toAbsolutePath());
    }

    private static boolean confirmFlag(String[] args) {
        for (String a : args) {
            if ("--yes".equalsIgnoreCase(a) || "-y".equalsIgnoreCase(a))
                return true;
        }
        return false;
    }

    private static void reset(boolean yes) throws SQLException {
        if (!yes) {
            System.out.print("This will DELETE all captured auth + command logs. "
                    + "Continue? [y/N] ");
            String line = new Scanner(System.in).nextLine().trim().toLowerCase();
            if (!line.equals("y") && !line.equals("yes")) {
                System.out.println("Aborted.");
                return;
            }
        }
        try (Connection c = DriverManager.getConnection(DB_URL);
                Statement s = c.createStatement()) {
            s.executeUpdate("DELETE FROM auth_logs;");
            s.executeUpdate("DELETE FROM command_logs;");
            try {
                s.executeUpdate("DELETE FROM http_request_logs;");
            } catch (SQLException ignored) {
            }
            // reset autoincrement counters too
            try {
                s.executeUpdate(
                        "DELETE FROM sqlite_sequence WHERE name IN ('auth_logs','command_logs','http_request_logs');");
            } catch (SQLException ignored) {
            }
        }
        System.out.println("Logs cleared.");
    }

    private static void interactiveMenu() throws Exception {
        Scanner in = new Scanner(System.in);
        while (true) {
            System.out.println();
            System.out.println("====== IoT Honeypot Console ======");
            System.out.println(" 1) Live stats             7) Export CSV");
            System.out.println(" 2) Recent auth attempts   8) Reset (clear DB)");
            System.out.println(" 3) Recent commands        9) Start SSH server");
            System.out.println(" 4) Recent HTTP requests  10) Start as <camera|router|...>");
            System.out.println(" 5) Top usernames          0) Quit");
            System.out.println(" 6) Top source IPs");
            System.out.print("> ");
            String pick = in.nextLine().trim();
            try {
                switch (pick) {
                    case "1" -> printStats();
                    case "2" -> tailAuthLogs(20);
                    case "3" -> tailCommandLogs(20);
                    case "4" -> tailHttpRequests(20);
                    case "5" -> topAttemptedUsers(10);
                    case "6" -> topSourceIps(10);
                    case "7" -> exportCsv("honeypot-export.csv", "all");
                    case "8" -> reset(false);
                    case "9" -> {
                        HoneypotServer.main(new String[] {});
                        return;
                    }
                    case "10" -> {
                        System.out.print("Profile [camera|router|doorlock|website|ssh|multi]: ");
                        String p = in.nextLine().trim();
                        System.setProperty("honeypot.profile", p.toUpperCase(java.util.Locale.ROOT));
                        HoneypotServer.main(new String[] {});
                        return;
                    }
                    case "0", "q", "quit" -> {
                        return;
                    }
                    default -> System.out.println("Pick a number 0-10.");
                }
            } catch (Exception e) {
                System.err.println("Error: " + e.getMessage());
            }
        }
    }

    // ---------------- Helpers ----------------

    private static int argInt(String[] args, int idx, int defVal) {
        if (idx >= args.length)
            return defVal;
        try {
            return Integer.parseInt(args[idx]);
        } catch (NumberFormatException e) {
            return defVal;
        }
    }

    private static void row(String label, Statement s, String sql) throws SQLException {
        row(label, s, sql, "0");
    }

    private static void row(String label, Statement s, String sql, String fallback)
            throws SQLException {
        try (ResultSet rs = s.executeQuery(sql)) {
            String v = rs.next() ? rs.getString(1) : null;
            if (v == null)
                v = fallback;
            System.out.printf("%-18s %s%n", label + ":", v);
        }
    }

    private static void printTable(ResultSet rs, List<String> header) throws SQLException {
        Map<String, Integer> widths = new LinkedHashMap<>();
        for (String h : header)
            widths.put(h, h.length());

        List<Map<String, String>> rows = new ArrayList<>();
        ResultSetMetaData md = rs.getMetaData();
        int cols = md.getColumnCount();

        while (rs.next()) {
            Map<String, String> row = new LinkedHashMap<>();
            for (int i = 1; i <= cols && i <= header.size(); i++) {
                String col = header.get(i - 1);
                String val = rs.getString(i);
                if (val == null)
                    val = "";
                row.put(col, val);
                widths.merge(col, Math.min(val.length(), 80), Math::max);
            }
            rows.add(row);
        }
        printRow(widths.keySet(), widths);
        printRule(widths);
        for (Map<String, String> r : rows)
            printRow(r.values(), widths);
    }

    private static void printRow(java.util.Collection<String> cells,
            Map<String, Integer> widths) {
        StringBuilder sb = new StringBuilder();
        int i = 0;
        for (String c : cells) {
            Integer w = new ArrayList<>(widths.values()).get(i++);
            String truncated = c.length() > w ? c.substring(0, w - 1) + "…" : c;
            sb.append(String.format("%-" + w + "s  ", truncated));
        }
        System.out.println(sb);
    }

    private static void printRule(Map<String, Integer> widths) {
        StringBuilder sb = new StringBuilder();
        for (Integer w : widths.values()) {
            for (int j = 0; j < w + 2; j++)
                sb.append('-');
        }
        System.out.println(sb);
    }

    /** Minimal RFC-4180 CSV escaping. */
    private static String csv(String s) {
        if (s == null)
            return "";
        boolean needsQuotes = s.indexOf(',') >= 0 || s.indexOf('"') >= 0
                || s.indexOf('\n') >= 0 || s.indexOf('\r') >= 0;
        String escaped = s.replace("\"", "\"\"");
        return needsQuotes ? "\"" + escaped + "\"" : escaped;
    }

    private static void printHelp() {
        String ts = java.time.ZonedDateTime.now().format(TS_FMT);
        System.out.println("IoT Honeypot CLI  (" + ts + ")");
        System.out.println("Usage: java -jar iot-honeypot.jar [command] [options]");
        System.out.println();
        System.out.println("Commands (no args -> run SSH server):");
        System.out.println("  --stats                 Print summary statistics");
        System.out.println("  --logs [N]              Last N auth attempts (default 20)");
        System.out.println("  --commands [N]          Last N shell commands (default 20)");
        System.out.println("  --requests [N]          Last N HTTP requests (default 20)");
        System.out.println("  --top-users [N]         Top attempted usernames");
        System.out.println("  --top-ips [N]           Top source IPs");
        System.out.println("  --watch                 Refresh stats every 5s");
        System.out.println("  --export <file> [auth|commands|http|all]   Export CSV");
        System.out.println("  --reset [--yes]         Wipe auth + command + http logs");
        System.out.println("  --serve                 Start the SSH server (default)");
        System.out.println("  --profile <name>        Start as a device profile");
        System.out.println("                           {ssh|website|router|camera|doorlock|multi}");
        System.out.println("  --menu                  Interactive console");
        System.out.println("  --help                  Show this help");
        System.out.println();
        System.out.println("Tunables (system properties):");
        System.out.println("  -Dhoneypot.profile=<name>     Default device persona");
        System.out.println("  -Dhoneypot.port=2222          SSH port");
        System.out.println("  -Dhoneypot.http.port=8080     HTTP port");
        System.out.println("  -Dhoneypot.rtsp.port=554      RTSP port");
        System.out.println("  -Dhoneypot.bind=0.0.0.0       Bind address");
    }
}
