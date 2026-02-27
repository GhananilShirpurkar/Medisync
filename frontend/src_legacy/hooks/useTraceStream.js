import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

/**
 * useTraceStream — subscribes to the backend WebSocket trace stream for a session.
 * Returns live trace events as they're emitted by agents.
 */
export function useTraceStream(sessionId) {
  const [events, setEvents] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    if (!sessionId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const url = `${WS_BASE}/ws/trace/${sessionId}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setConnected(true);
      // Heartbeat every 25s to keep connection alive
      reconnectTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping');
      }, 25_000);
    };

    ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data);
        if (event === 'pong') return;
        setEvents((prev) => [...prev, event]);
      } catch (_) {}
    };

    ws.onclose = () => {
      setConnected(false);
      clearInterval(reconnectTimer.current);
      // Reconnect after 3s
      setTimeout(connect, 3_000);
    };

    ws.onerror = () => ws.close();
    wsRef.current = ws;
  }, [sessionId]);

  useEffect(() => {
    connect();
    return () => {
      clearInterval(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const clearEvents = useCallback(() => setEvents([]), []);

  return { events, connected, clearEvents };
}
