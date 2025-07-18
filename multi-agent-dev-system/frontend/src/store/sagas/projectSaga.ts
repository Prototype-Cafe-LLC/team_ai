import { call, put, takeLatest, all } from 'redux-saga/effects';
import axios from 'axios';
import {
  fetchProjectsRequest,
  fetchProjectsSuccess,
  fetchProjectsFailure,
  createProjectRequest,
  createProjectSuccess,
  createProjectFailure,
  pauseProjectRequest,
  pauseProjectSuccess,
  pauseProjectFailure,
  resumeProjectRequest,
  resumeProjectSuccess,
  resumeProjectFailure
} from '../slices/projectSlice';
import { connectWebSocket } from '../slices/webSocketSlice';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// API calls
const api = {
  fetchProjects: () => axios.get(`${API_BASE_URL}/api/projects`),
  createProject: (name: string, requirements: string) => 
    axios.post(`${API_BASE_URL}/api/projects`, { name, requirements }),
  pauseProject: (projectId: string) => 
    axios.post(`${API_BASE_URL}/api/projects/${projectId}/pause`),
  resumeProject: (projectId: string, direction?: any) => 
    axios.post(`${API_BASE_URL}/api/projects/${projectId}/resume`, direction ? { direction } : {})
};

// Sagas
function* fetchProjectsSaga() {
  try {
    const response: { data: any } = yield call(api.fetchProjects);
    yield put(fetchProjectsSuccess(response.data));
  } catch (error: any) {
    yield put(fetchProjectsFailure(error.message || 'Failed to fetch projects'));
  }
}

function* createProjectSaga(action: ReturnType<typeof createProjectRequest>) {
  try {
    const { name, requirements } = action.payload;
    const response: { data: any } = yield call(api.createProject, name, requirements);
    yield put(createProjectSuccess(response.data));
    
    // Automatically connect WebSocket for the new project
    yield put(connectWebSocket(response.data.project_id));
  } catch (error: any) {
    yield put(createProjectFailure(error.message || 'Failed to create project'));
  }
}

function* pauseProjectSaga(action: ReturnType<typeof pauseProjectRequest>) {
  try {
    yield call(api.pauseProject, action.payload);
    yield put(pauseProjectSuccess(action.payload));
    
    // Refresh projects list
    yield put(fetchProjectsRequest());
  } catch (error: any) {
    yield put(pauseProjectFailure(error.message || 'Failed to pause project'));
  }
}

function* resumeProjectSaga(action: ReturnType<typeof resumeProjectRequest>) {
  try {
    const { projectId, direction } = action.payload;
    yield call(api.resumeProject, projectId, direction);
    yield put(resumeProjectSuccess(projectId));
    
    // Refresh projects list
    yield put(fetchProjectsRequest());
  } catch (error: any) {
    yield put(resumeProjectFailure(error.message || 'Failed to resume project'));
  }
}

// Root saga
export default function* projectSaga() {
  yield all([
    takeLatest(fetchProjectsRequest.type, fetchProjectsSaga),
    takeLatest(createProjectRequest.type, createProjectSaga),
    takeLatest(pauseProjectRequest.type, pauseProjectSaga),
    takeLatest(resumeProjectRequest.type, resumeProjectSaga)
  ]);
}