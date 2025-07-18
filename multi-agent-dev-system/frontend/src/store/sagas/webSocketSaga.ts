import { eventChannel, END } from 'redux-saga';
import { call, put, take, takeEvery, fork, cancel, cancelled, select } from 'redux-saga/effects';
import {
  connectWebSocket,
  webSocketConnected,
  webSocketDisconnected,
  webSocketError,
  disconnectWebSocket,
  addMessage,
  receiveWebSocketMessage
} from '../slices/webSocketSlice';
import { updateProjectStatus } from '../slices/projectSlice';
import { Message, WebSocketMessage, Phase, ProjectStatus } from '../types';
import { RootState } from '../store';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

function createWebSocketChannel(socket: WebSocket) {
  return eventChannel(emit => {
    socket.onopen = () => {
      emit({ type: 'connected' });
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        emit({ type: 'message', data });
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    socket.onerror = (error) => {
      emit({ type: 'error', error });
    };

    socket.onclose = () => {
      emit(END);
    };

    return () => {
      socket.close();
    };
  });
}

function* handleWebSocketMessage(data: WebSocketMessage) {
  const timestamp = new Date();
  
  if (data.type === 'agent_output') {
    const message: Message = {
      id: `${Date.now()}-${Math.random()}`,
      type: 'agent_output',
      content: data.content || '',
      agent_id: data.agent_id,
      timestamp
    };
    yield put(addMessage(message));
  } else if (data.type === 'phase_transition') {
    const message: Message = {
      id: `${Date.now()}-${Math.random()}`,
      type: 'system',
      content: `Transitioning to ${data.to_phase} phase`,
      timestamp
    };
    yield put(addMessage(message));
    
    // Update current phase in project
    const currentProject = yield select((state: RootState) => state.project.currentProject);
    if (currentProject && data.to_phase) {
      yield put(updateProjectStatus({
        projectId: currentProject.project_id,
        status: ProjectStatus.RUNNING
      }));
    }
  } else if (data.type === 'error') {
    const message: Message = {
      id: `${Date.now()}-${Math.random()}`,
      type: 'error',
      content: data.message || 'An error occurred',
      timestamp
    };
    yield put(addMessage(message));
  } else if (data.type === 'connection') {
    const message: Message = {
      id: `${Date.now()}-${Math.random()}`,
      type: 'system',
      content: data.message || 'Connected to project',
      timestamp
    };
    yield put(addMessage(message));
  } else {
    // Handle other message types
    const message: Message = {
      id: `${Date.now()}-${Math.random()}`,
      type: 'system',
      content: JSON.stringify(data),
      timestamp,
      metadata: data
    };
    yield put(addMessage(message));
  }
}

function* watchWebSocket(socket: WebSocket) {
  const channel = yield call(createWebSocketChannel, socket);
  
  try {
    while (true) {
      const event = yield take(channel);
      
      if (event.type === 'connected') {
        yield put(webSocketConnected());
        yield put(addMessage({
          id: `${Date.now()}-connected`,
          type: 'system',
          content: 'Connected to backend',
          timestamp: new Date()
        }));
      } else if (event.type === 'message') {
        yield fork(handleWebSocketMessage, event.data);
      } else if (event.type === 'error') {
        yield put(webSocketError('WebSocket error occurred'));
      }
    }
  } finally {
    if (yield cancelled()) {
      channel.close();
    }
    yield put(webSocketDisconnected());
    yield put(addMessage({
      id: `${Date.now()}-disconnected`,
      type: 'system',
      content: 'Disconnected from backend',
      timestamp: new Date()
    }));
  }
}

function* connectWebSocketSaga(action: ReturnType<typeof connectWebSocket>) {
  const projectId = action.payload;
  const socket = new WebSocket(`${WS_BASE_URL}/api/ws/${projectId}`);
  
  const task = yield fork(watchWebSocket, socket);
  
  // Wait for disconnect action
  yield take(disconnectWebSocket.type);
  yield cancel(task);
}

function* handleReceiveWebSocketMessage(action: ReturnType<typeof receiveWebSocketMessage>) {
  yield fork(handleWebSocketMessage, action.payload);
}

export default function* webSocketSaga() {
  yield takeEvery(connectWebSocket.type, connectWebSocketSaga);
  yield takeEvery(receiveWebSocketMessage.type, handleReceiveWebSocketMessage);
}