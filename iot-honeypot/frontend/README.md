# 🛡️ Honeynet Dashboard

React 18 + Vite + TypeScript dashboard for the IoT Honeynet Research Platform.

## Features

- 🔐 JWT login + refresh-token rotation
- 🌗 Light / Dark mode toggle (persisted in `localStorage`)
- 📊 Real-time statistics (Recharts: line / bar / pie / area)
- 🌍 Live attack map (Leaflet + OpenStreetMap)
- 📡 WebSocket live attack stream
- 📱 Fully responsive layout (mobile drawer, fluid grid)
- 🎨 Material UI v5 theme system

## Quick start

```bash
cp .env.example .env
npm install
npm run dev
```

Dashboard will be available at `http://localhost:5173`.
Backend is expected at `http://localhost:8000` (proxied through Vite at `/api`).

## Demo credentials

| Role    | Username | Password   |
|---------|----------|------------|
| Admin   | `admin`  | `admin123` |
| Analyst | `analyst`| `analyst123` |

(Only active when `VITE_ENABLE_DEMO_MODE=true`)

## Scripts

| Script           | Purpose                  |
|------------------|--------------------------|
| `npm run dev`    | Vite dev server (HMR)    |
| `npm run build`  | Production bundle        |
| `npm run preview`| Serve built bundle       |
| `npm run lint`   | ESLint                   |
| `npm test`       | Vitest one-shot run      |