import { useEffect } from 'react';
import { api } from '../api';

export function useBoardRealtime(boardId: number | undefined, onEvent: () => void) {
  useEffect(() => {
    if (!boardId) return;
    if (!localStorage.getItem('teamflow_token')) return;
    let socket: WebSocket | null = null;
    let retry: number | undefined;
    let stopped = false;
    let delay = 500;

    const scheduleRetry = () => {
      if (stopped || retry !== undefined) return;
      retry = window.setTimeout(() => {
        retry = undefined;
        void connect();
      }, delay);
      delay = Math.min(delay * 2, 10000);
    };

    const connect = async () => {
      if (stopped) return;
      const ticketResponse = await api<{ ticket: string }>('/auth/ws-ticket', { method: 'POST' }).catch(() => null);
      if (!ticketResponse || stopped) {
        scheduleRetry();
        return;
      }
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      socket = new WebSocket(`${protocol}//${window.location.host}/ws/boards/${boardId}?ticket=${encodeURIComponent(ticketResponse.ticket)}`);
      socket.onopen = () => { delay = 500; };
      socket.onmessage = () => onEvent();
      socket.onclose = () => {
        scheduleRetry();
      };
      socket.onerror = () => socket?.close();
    };

    connect();
    return () => {
      stopped = true;
      if (retry) window.clearTimeout(retry);
      socket?.close();
    };
  }, [boardId, onEvent]);
}
