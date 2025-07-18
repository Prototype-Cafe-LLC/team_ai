import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Project, ProjectStatus } from '../types';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
}

const initialState: ProjectState = {
  projects: [],
  currentProject: null,
  loading: false,
  error: null
};

const projectSlice = createSlice({
  name: 'project',
  initialState,
  reducers: {
    // Fetch projects
    fetchProjectsRequest: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchProjectsSuccess: (state, action: PayloadAction<Project[]>) => {
      state.loading = false;
      state.projects = action.payload;
    },
    fetchProjectsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Create project
    createProjectRequest: (state, action: PayloadAction<{ name: string; requirements: string }>) => {
      state.loading = true;
      state.error = null;
    },
    createProjectSuccess: (state, action: PayloadAction<Project>) => {
      state.loading = false;
      state.projects.push(action.payload);
      state.currentProject = action.payload;
    },
    createProjectFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Select project
    selectProject: (state, action: PayloadAction<string>) => {
      const project = state.projects.find(p => p.project_id === action.payload);
      state.currentProject = project || null;
    },

    // Update project status
    updateProjectStatus: (state, action: PayloadAction<{ projectId: string; status: ProjectStatus }>) => {
      const project = state.projects.find(p => p.project_id === action.payload.projectId);
      if (project) {
        project.status = action.payload.status;
      }
      if (state.currentProject?.project_id === action.payload.projectId) {
        state.currentProject.status = action.payload.status;
      }
    },

    // Pause project
    pauseProjectRequest: (state, action: PayloadAction<string>) => {
      state.loading = true;
      state.error = null;
    },
    pauseProjectSuccess: (state, action: PayloadAction<string>) => {
      state.loading = false;
      const project = state.projects.find(p => p.project_id === action.payload);
      if (project) {
        project.status = ProjectStatus.PAUSED;
      }
      if (state.currentProject?.project_id === action.payload) {
        state.currentProject.status = ProjectStatus.PAUSED;
      }
    },
    pauseProjectFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Resume project
    resumeProjectRequest: (state, action: PayloadAction<{ projectId: string; direction?: any }>) => {
      state.loading = true;
      state.error = null;
    },
    resumeProjectSuccess: (state, action: PayloadAction<string>) => {
      state.loading = false;
      const project = state.projects.find(p => p.project_id === action.payload);
      if (project) {
        project.status = ProjectStatus.RUNNING;
      }
      if (state.currentProject?.project_id === action.payload) {
        state.currentProject.status = ProjectStatus.RUNNING;
      }
    },
    resumeProjectFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Clear error
    clearError: (state) => {
      state.error = null;
    }
  }
});

export const {
  fetchProjectsRequest,
  fetchProjectsSuccess,
  fetchProjectsFailure,
  createProjectRequest,
  createProjectSuccess,
  createProjectFailure,
  selectProject,
  updateProjectStatus,
  pauseProjectRequest,
  pauseProjectSuccess,
  pauseProjectFailure,
  resumeProjectRequest,
  resumeProjectSuccess,
  resumeProjectFailure,
  clearError
} = projectSlice.actions;

export default projectSlice.reducer;