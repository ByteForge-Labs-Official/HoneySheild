import { io, Socket } from 'socket.io-client';
import { tokenStorage } from '@/services/storage/tokenStorage';

const WS_URL = import.meta.env.VITE_WS_URL ?? '/api/v1/ws';

type AttackHandler = (msg: unknown) => void;

class LiveSocketService {
  private socket: Socket | null = null;
  private handlers = new Map<string, Set<AttackHandler>>();

  connect(): void {
    if (this.socket?.connected) return;
    const token = tokenStorage.getAccessToken();
    this.socket = io(WS_URL, {
      transports: ['websocket'],
      auth: token ? { token } : undefined,
      reconnection: true,
      reconnectionDelay: 1500,
      reconnectionDelayMax: 10_000,
    });
    this.socket.on('attack', (payload: unknown) => this.emit('attack', payload));
    this.socket.on('alert', (payload: unknown) => this.emit('alert', payload));
  }

  disconnect(): void {
    this.socket?.disconnect();
    this.socket = null;
  }

  on(event: string, fn: AttackHandler): () => void {
    if (!this.handlers.has(event)) this.handlers.set(event, new Set());
    this.handlers.get(event)!.add(fn);
    return () => this.handlers.get(event)?.delete(fn);
  }

  private emit(event: string, payload: unknown): void {
    this.handlers.get(event)?.forEach((fn) => fn(payload));
  }
}

export const liveSocket = new LiveSocketService();