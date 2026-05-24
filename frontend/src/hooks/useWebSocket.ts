import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/store/authStore';

type WebSocketMessage = {
  type: string;
  data?: unknown;
  // Present on resource_changed broadcasts (see backend notify_resource).
  resource?: string;
  action?: string;
  // Present on error frames.
  message?: string;
};

export const useWebSocket = (onMessage?: (message: WebSocketMessage) => void) => {
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();
  // Set when we close on purpose (unmount / logout) so the onclose handler
  // doesn't fire the 5s reconnect against a now-stale closure.
  const closedIntentionally = useRef(false);
  // After #42 the access token is an httpOnly cookie JS can't read; it
  // rides the WS upgrade handshake automatically (same-origin /ws proxy),
  // so the server authenticates from the cookie. We only need to know
  // *whether* the user is logged in to decide when to connect.
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const connect = useCallback(() => {
    if (!isAuthenticated) return;

    try {
      closedIntentionally.current = false;
      const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const WS_URL = import.meta.env.VITE_WS_URL || `${scheme}://${window.location.host}/ws`;
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        // No auth message needed — the httpOnly cookie authenticated the
        // handshake server-side.
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

        // Don't reconnect if we closed deliberately (unmount / logout).
        if (closedIntentionally.current) return;
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
  }, [isAuthenticated, onMessage]);

  const disconnect = useCallback(() => {
    closedIntentionally.current = true;
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
    send({ action: 'unsubscribe_team', team_id: teamId });
  }, [send]);

  useEffect(() => {
    if (isAuthenticated) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, connect, disconnect]);

  return {
    isConnected,
    send,
    subscribeToTeam,
    unsubscribeFromTeam,
  };
};
