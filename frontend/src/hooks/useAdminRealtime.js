import { useEffect, useRef, useState, useCallback } from 'react';

const SOCKET_URL = "ws://localhost:8000/api/v1/admin/ws";

export const useAdminRealtime = (onEvent) => {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    console.log("Connecting to Admin WebSocket...");
    const socket = new WebSocket(SOCKET_URL);

    socket.onopen = () => {
      console.log("Admin WebSocket connected");
      setIsConnected(true);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (onEvent) {
          onEvent(message);
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    socket.onclose = () => {
      console.log("Admin WebSocket disconnected");
      setIsConnected(false);
      // Attempt reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    };

    socket.onerror = (err) => {
      console.error("Admin WebSocket error:", err);
      socket.close();
    };

    socketRef.current = socket;
  }, [onEvent]);

  useEffect(() => {
    connect();
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const send = (data) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  };

  return { isConnected, send };
};
