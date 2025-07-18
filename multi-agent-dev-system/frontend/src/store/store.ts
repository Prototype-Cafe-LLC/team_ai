import { configureStore } from '@reduxjs/toolkit';
import createSagaMiddleware from 'redux-saga';
import projectReducer from './slices/projectSlice';
import webSocketReducer from './slices/webSocketSlice';
import rootSaga from './sagas';

const sagaMiddleware = createSagaMiddleware();

export const store = configureStore({
  reducer: {
    project: projectReducer,
    webSocket: webSocketReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: ['webSocket/addMessage'],
        // Ignore these field paths in all actions
        ignoredActionPaths: ['payload.timestamp'],
        // Ignore these paths in the state
        ignoredPaths: ['webSocket.messages']
      }
    }).concat(sagaMiddleware)
});

sagaMiddleware.run(rootSaga);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;