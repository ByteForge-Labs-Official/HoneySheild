import { useEffect } from 'react';
import { useAppDispatch } from '@/store/hooks';
import { attacksActions } from '@/store/slices/attacksSlice';
import { alertsActions } from '@/store/slices/alertsSlice';
import { liveSocket } from '@/services/socket/liveSocket';
import type { Attack } from '@/types/attack';
import type { Alert } from '@/types/alert';

export function useLiveAttacks(): void {
  const dispatch = useAppDispatch();
  useEffect(() => {
    liveSocket.connect();
    const offA = liveSocket.on('attack', (p) =>
      dispatch(attacksActions.pushLive(p as Attack)),
    );
    const offL = liveSocket.on('alert', (p) =>
      dispatch(alertsActions.pushLive(p as Alert)),
    );
    return () => {
      offA();
      offL();
    };
  }, [dispatch]);
}