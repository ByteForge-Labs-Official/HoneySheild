# Multi-stage build for the Honeynet Dashboard (Vite + React + TS)

# ---------- build ----------
FROM node:20-alpine AS build
WORKDIR /app

# Cache deps
COPY package.json ./
RUN npm install --no-audit --no-fund

# Build
COPY tsconfig.json tsconfig.node.json vite.config.ts index.html ./
COPY src ./src
COPY public ./public 2>/dev/null || true

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_WS_URL=/api/v1/ws
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_URL=$VITE_WS_URL

RUN npm run build

# ---------- runtime ----------
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD wget -q -O - http://localhost/ >/dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]