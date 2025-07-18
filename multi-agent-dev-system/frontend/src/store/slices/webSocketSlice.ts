import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Message } from '../types';

interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  projectId: string | null;
  messages: Message[];
  error: string | null;
}

const initialState: WebSocketState = {
  connected: false,
  connecting: false,
  projectId: null,
  messages: [],
  error: null
};

const webSocketSlice = createSlice({
  name: 'webSocket',
  initialState,
  reducers: {
    // Connect to WebSocket
    connectWebSocket: (state, action: PayloadAction<string>) => {
      state.connecting = true;
      state.projectId = action.payload;
      state.error = null;
    },
    webSocketConnected: (state) => {
      state.connecting = false;
      state.connected = true;
    },
    webSocketDisconnected: (state) => {
      state.connecting = false;
      state.connected = false;
    },
    webSocketError: (state, action: PayloadAction<string>) => {
      state.connecting = false;
      state.error = action.payload;
    },

    // Disconnect WebSocket
    disconnectWebSocket: (state) => {
      state.connected = false;
      state.connecting = false;
      state.projectId = null;
    },

    // Add message
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(action.payload);
    },

    // Clear messages
    clearMessages: (state) => {
      state.messages = [];
    },

    // Handle WebSocket messages
    receiveWebSocketMessage: (state, action: PayloadAction<any>) => {
      // This action is handled by saga
    }
  }
});

export const {
  connectWebSocket,
  webSocketConnected,
  webSocketDisconnected,
  webSocketError,
  disconnectWebSocket,
  addMessage,
  clearMessages,
  receiveWebSocketMessage
} = webSocketSlice.actions;

export default webSocketSlice.reducer;