import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';

interface Message {
  id: string;
  type: 'agent_output' | 'system' | 'error' | 'phase_transition';
  content: string;
  agent_id?: string;
  timestamp: Date;
  metadata?: any;
}

interface WebSocketContextType {
  connected: boolean;
  messages: Message[];
  connect: (projectId: string) => void;
  disconnect: () => void;
  clearMessages: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);

  const connect = useCallback((projectId: string) => {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.close();
    }

    const ws = new WebSocket(`${WS_BASE_URL}/api/ws/${projectId}`);

    ws.onopen = () => {
      setConnected(true);
      addMessage('system', 'Connected to project');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      addMessage('error', 'WebSocket connection error');
    };

    ws.onclose = () => {
      setConnected(false);
      addMessage('system', 'Disconnected from project');
    };

    setSocket(ws);
  }, [socket]);

  const disconnect = useCallback(() => {
    if (socket) {
      socket.close();
      setSocket(null);
    }
  }, [socket]);

  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'agent_output') {
      addMessage('agent_output', data.content, data.agent_id);
    } else if (data.type === 'phase_transition') {
      addMessage('system', `Transitioning to ${data.to_phase} phase`);
    } else if (data.type === 'error') {
      addMessage('error', data.message || 'An error occurred');
    } else {
      addMessage('system', JSON.stringify(data));
    }
  };

  const addMessage = (type: Message['type'], content: string, agent_id?: string) => {
    const message: Message = {
      id: `${Date.now()}-${Math.random()}`,
      type,
      content,
      agent_id,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  };

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  useEffect(() => {
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [socket]);

  const value: WebSocketContextType = {
    connected,
    messages,
    connect,
    disconnect,
    clearMessages
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}