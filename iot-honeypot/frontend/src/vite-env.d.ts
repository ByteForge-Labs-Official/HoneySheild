/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_TILE_URL: string;
  readonly VITE_TILE_ATTRIBUTION: string;
  readonly VITE_ENABLE_LIVE_MAP: string;
  readonly VITE_ENABLE_DEMO_MODE: string;
  readonly VITE_API_PROXY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module '*.svg' {
  const content: string;
  export default content;
}