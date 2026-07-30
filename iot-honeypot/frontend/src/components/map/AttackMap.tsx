import React, { useEffect, useRef, useMemo } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { MapContainer, TileLayer, Popup, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import type { Attack, AttackStats } from '@/types/attack';

const TILE_URL = import.meta.env.VITE_TILE_URL ?? 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const TILE_ATTR =
  import.meta.env.VITE_TILE_ATTRIBUTION ?? '© OpenStreetMap contributors';

const SEVERITY_COLOR: Record<string, string> = {
  low: '#06b6d4',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#7f1d1d',
};

interface AttackMapProps {
  attacks?: Attack[];
  geo?: AttackStats['by_country'];
  height?: number | string;
  zoom?: number;
  center?: [number, number];
  live?: boolean;
}

export const AttackMap: React.FC<AttackMapProps> = ({
  attacks,
  geo,
  height = 'calc(100vh - 200px)',
  zoom = 2,
  center = [20, 0],
  live = false,
}) => {
  const markerIcon = useRef<L.Icon | null>(null);

  useEffect(() => {
    // Fix leaflet icon path under Vite
    markerIcon.current = L.icon({
      iconUrl:
        'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      iconRetinaUrl:
        'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      shadowUrl:
        'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    });
  }, []);

  const attackPoints = useMemo(
    () =>
      (attacks ?? [])
        .filter((a) => a.latitude !== undefined && a.longitude !== undefined)
        .slice(0, 200) as Array<Attack & { latitude: number; longitude: number }>,
    [attacks],
  );

  const geoPoints = useMemo(
    () =>
      (geo ?? [])
        .filter((g) => g.lat !== undefined && g.lon !== undefined)
        .slice(0, 200) as Array<{ country: string; count: number; lat: number; lon: number }>,
    [geo],
  );

  return (
    <Box
      sx={{
        height,
        width: '100%',
        borderRadius: 2,
        overflow: 'hidden',
        border: 1,
        borderColor: 'divider',
        position: 'relative',
      }}
    >
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom
        style={{ height: '100%', width: '100%' }}
        worldCopyJump
      >
        <TileLayer url={TILE_URL} attribution={TILE_ATTR} />

        {/* Geo aggregated heat circles */}
        {geoPoints.map((p) => (
          <CircleMarker
            key={`geo-${p.country}`}
            center={[p.lat, p.lon]}
            radius={Math.min(40, Math.max(6, Math.log10(p.count) * 8))}
            pathOptions={{
              color: '#ef4444',
              fillColor: '#ef4444',
              fillOpacity: 0.35,
              weight: 1,
            }}
          >
            <Popup>
              <Typography variant="subtitle2">{p.country}</Typography>
              <Typography variant="body2">{p.count.toLocaleString()} attacks</Typography>
            </Popup>
          </CircleMarker>
        ))}

        {/* Live attack points */}
        {attackPoints.map((a) => (
          <CircleMarker
            key={a.id}
            center={[a.latitude, a.longitude]}
            radius={6}
            pathOptions={{
              color: SEVERITY_COLOR[a.severity] ?? '#1976d2',
              fillColor: SEVERITY_COLOR[a.severity] ?? '#1976d2',
              fillOpacity: 0.9,
              weight: 2,
            }}
          >
            <Popup>
              <Typography variant="caption" color="text.secondary">
                {new Date(a.timestamp).toLocaleString()}
              </Typography>
              <Typography variant="subtitle2">{a.source_ip}</Typography>
              <Typography variant="body2">
                {a.country} → {a.honeypot_name ?? a.protocol.toUpperCase()}
              </Typography>
              <Typography variant="caption">Severity: {a.severity}</Typography>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {live && (
        <Box
          sx={{
            position: 'absolute',
            top: 12,
            right: 12,
            zIndex: 1000,
            bgcolor: 'background.paper',
            color: 'text.primary',
            px: 1.5,
            py: 0.5,
            borderRadius: 1,
            boxShadow: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <CircularProgress size={12} color="success" />
          <Typography variant="caption" fontWeight={600}>
            LIVE
          </Typography>
        </Box>
      )}
    </Box>
  );
};