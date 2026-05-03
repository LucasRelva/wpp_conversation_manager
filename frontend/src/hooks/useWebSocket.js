import { useEffect, useCallback, useRef, useState } from 'react';

const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export const useWebSocket = (agentId) => {
      const ws = useRef(null);
      const reconnectTimeout = useRef(null);
      const shouldReconnect = useRef(true);
      const [isConnected, setIsConnected] = useState(false);
      const [messages, setMessages] = useState([]);

      useEffect(() => {
            // Don't connect if no agent ID
            if (!agentId) return;

            shouldReconnect.current = true;

            const clearReconnectTimeout = () => {
                  if (reconnectTimeout.current) {
                        clearTimeout(reconnectTimeout.current);
                        reconnectTimeout.current = null;
                  }
            };

            const connectWebSocket = () => {
                  try {
                        ws.current = new WebSocket(`${WS_BASE_URL}/ws/conversations`);

                        ws.current.onopen = () => {
                              console.log('WebSocket connected');
                              setIsConnected(true);

                              // Register agent
                              ws.current.send(JSON.stringify({
                                    type: 'register_agent',
                                    agent_id: agentId
                              }));
                        };

                        ws.current.onmessage = (event) => {
                              try {
                                    const message = JSON.parse(event.data);
                                    setMessages(prev => [message, ...prev].slice(0, 100)); // Keep last 100
                              } catch (e) {
                                    console.error('Failed to parse WebSocket message:', e);
                              }
                        };

                        ws.current.onerror = (error) => {
                              console.error('WebSocket error:', error);
                              setIsConnected(false);
                        };

                        ws.current.onclose = () => {
                              console.log('WebSocket disconnected');
                              setIsConnected(false);

                              if (!shouldReconnect.current) return;

                              // Attempt reconnection after 3 seconds
                              clearReconnectTimeout();
                              reconnectTimeout.current = setTimeout(connectWebSocket, 3000);
                        };
                  } catch (error) {
                        console.error('Failed to create WebSocket:', error);
                        setIsConnected(false);
                  }
            };

            connectWebSocket();

            return () => {
                  shouldReconnect.current = false;
                  clearReconnectTimeout();
                  if (ws.current) {
                        ws.current.close();
                  }
            };
      }, [agentId]);

      const send = useCallback((message) => {
            if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                  ws.current.send(JSON.stringify(message));
            }
      }, []);

      return {
            isConnected,
            messages,
            send
      };
};
