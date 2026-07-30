package com.security.honeypot;

import java.util.List;
import java.util.Locale;

/**
 * DeviceProfile
 *
 * Selects which fake services the honeypot exposes so the operator
 * can spin up a believable copy of a specific device class with one
 * command. Each profile maps to a real-world device type IoT
 * scanners explicitly target.
 */
public enum DeviceProfile {

    /** Pure SSH shell, headless Linux server. */
    SSH_ONLY("Headless Linux Server",
            List.of("ssh")),

    /** Camera/doorlock style web admin only (no SSH). */
    WEBSITE("Generic Web Admin Panel",
            List.of("http")),

    /** Old consumer router: web admin + SSH backdoor. */
    ROUTER("TP-Link/Netgear-style SOHO Router",
            List.of("http", "ssh")),

    /** IP camera with web admin + ONVIF/RTSP motion. */
    CAMERA("Hikvision/Dahua-style IP Camera",
            List.of("http", "rtsp", "ssh")),

    /** Smart door lock with vendor mobile-style JSON API. */
    DOORLOCK("August/Yale-style Smart Door Lock",
            List.of("http")),

    /** Kitchen-sink persona; for lab demos. */
    MULTI("Multi-service PoC",
            List.of("http", "rtsp", "ssh"));

    public final String displayName;
    public final List<String> services;

    DeviceProfile(String displayName, List<String> services) {
        this.displayName = displayName;
        this.services = services;
    }

    /** Case-insensitive lookup; falls back to ROUTER. */
    public static DeviceProfile parse(String raw) {
        if (raw == null || raw.isBlank()) return ROUTER;
        try {
            return DeviceProfile.valueOf(raw.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException e) {
            return ROUTER;
        }
    }
}
