package com.security.honeypot;

import java.util.regex.Pattern;

/**
 * Sanitizer
 *
 * Defense-in-depth for every attacker-controlled string before it is
 *   (a) written back to the attacker's session  -> strip terminal escapes
 *   (b) persisted to SQLite                      -> strip nulls/control chars
 *   (c) reflected into canned responses          -> strip path-traversal characters
 *
 * These are *not* a substitute for prepared statements (bind variables
 * are the only real defense against SQL injection). They exist to:
 *   - keep ANSI/CSI escape sequences from rewriting the operator's terminal
 *   - keep null bytes and other control chars from corrupting logs
 *   - keep embedded newlines from breaking CSV exports
 *
 * Rule reference (audit 2026-07-28):
 *   Rule 2 (Input Sanitization & Path Traversal)
 */
public final class Sanitizer {

    /** Max length of a single attacker-supplied line; anything longer is truncated. */
    public static final int MAX_LINE_LEN = 1024;

    /** Max length of a single attacker-supplied header / form value. */
    public static final int MAX_VALUE_LEN = 4096;

    /**
     * Matches CSI / OSC / DCS / APC / PM sequences: ESC [ ... letter,
     * ESC ] ... BEL, and the single-char ESC itself. Covers the most
     * common terminal-redirection attacks.
     */
    private static final Pattern ANSI_ESCAPE = Pattern.compile(
            // CSI: ESC [ ... <0x40-0x7E>
            "\u001B\\[[\\x30-\\x3F]*[\\x20-\\x2F]*[\\x40-\\x7E]"
                    // OSC / DCS / PM / APC: ESC <X> ... <terminator>
                    + "|\u001B[P^_].*?(?:\u0007|\u001B\\\\)"
                    // bare ESC
                    + "|\u001B"
    );

    /** Strips path-traversal characters without nuking legitimate text. */
    private static final Pattern PATH_TRAVERSAL =
            Pattern.compile("(?:%2[eE]|\\.\\./|\\.\\.\\\\)");

    /**
     * Strip control characters (< 0x20, plus DEL 0x7F) except for tab,
     * LF and CR which are meaningful for line-based protocols. Also
     * drops the explicit null byte regardless of context.
     */
    public static String stripControlChars(String s) {
        if (s == null || s.isEmpty()) return "";
        StringBuilder out = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\n' || c == '\r' || c == '\t') {
                out.append(c);
            } else if (c < 0x20 || c == 0x7F) {
                out.append(' ');
            } else {
                out.append(c);
            }
        }
        return out.toString();
    }

    /**
     * Strip ANSI / OSC escape sequences. Useful when echoing data back
     * to the attacker's own terminal so they can't redirect the output
     * by injecting CSI sequences.
     */
    public static String stripAnsi(String s) {
        if (s == null || s.isEmpty()) return "";
        return ANSI_ESCAPE.matcher(s).replaceAll("");
    }

    /**
     * Strip path-traversal sequences in a safe-for-logging form.
     * (We never pass attacker input to the filesystem, but logs that
     * contain "../" can confuse downstream tools.)
     */
    public static String stripPathTraversal(String s) {
        if (s == null || s.isEmpty()) return "";
        return PATH_TRAVERSAL.matcher(s).replaceAll("");
    }

    /**
     * Hard-bounded, scrubbed, single-line version of an attacker
     * command. Used by the SSH shell and any other text-stream handler.
     * Combines all of: max length, ANSI strip, control-char strip,
     * path-traversal strip.
     */
    public static String cleanLine(String raw) {
        if (raw == null) return "";
        String s = raw;
        if (s.length() > MAX_LINE_LEN) {
            s = s.substring(0, MAX_LINE_LEN);
        }
        s = stripAnsi(s);
        s = stripControlChars(s);
        s = stripPathTraversal(s);
        return s.trim();
    }

    /**
     * Multi-value variant for HTTP form fields / header values.
     */
    public static String cleanValue(String raw) {
        if (raw == null) return "";
        String s = raw;
        if (s.length() > MAX_VALUE_LEN) {
            s = s.substring(0, MAX_VALUE_LEN);
        }
        s = stripAnsi(s);
        s = stripControlChars(s);
        s = stripPathTraversal(s);
        return s.trim();
    }
}