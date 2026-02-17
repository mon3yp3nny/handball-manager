import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/store/authStore';

type WebSocketMessage = {
  type: string;
  data?: unknown;
};

export const useWebSocket = (onMessage?: (message: WebSocketMessage) => void) => {
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();
  const token = useAuthStore((state) => state.token);

  const connect = useCallback(() => {
    if (!token) return;

    try {
      const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`;
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Send authentication
        if (ws.current) {
          ws.current.send(JSON.stringify({ token }));
        }
      };

      ws.current.onmessage = (event) => {
        let message: WebSocketMessage;
        try {
          message = JSON.parse(event.data);
        } catch {
          console.error('WebSocket: invalid JSON received');
          return;
        }
        console.log('WebSocket message:', message);
        
        if (message.type === 'error') {
          console.error('WebSocket error:', message.message);
          return;
        }
        
        if (message.type === 'connected') {
          console.log('Authenticated with WebSocket');
        }
        
        onMessage?.(message);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Try to reconnect after 5 seconds
        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, 5000);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [token, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    if (ws.current) {
      ws.current.close();
    }
  }, []);

  const send = useCallback((message: object) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  }, []);

  const subscribeToTeam = useCallback((teamId: string) => {
    send({ action: 'subscribe_team', team_id: teamId });
  }, [send]);

  const unsubscribeFromTeam = useCallback((teamId: string) => {
    send({ action: 'unsubscribe_team', team_id });
  }, [send]);

  useEffect(() => {
    if (token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [token, connect, disconnect]);

  return {
    isConnected,
    send,
    subscribeToTeam,
    unsubscribeFromTeam,
  };
};
