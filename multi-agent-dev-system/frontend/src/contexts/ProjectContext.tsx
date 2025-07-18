import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import axios from 'axios';

interface Project {
  project_id: string;
  name: string;
  status: string;
  current_phase?: string;
  created_at: string;
}

interface ProjectContextType {
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  createProject: (name: string, requirements: string) => Promise<string>;
  selectProject: (projectId: string) => void;
  pauseProject: (projectId: string) => Promise<void>;
  resumeProject: (projectId: string) => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/projects`);
      setProjects(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch projects');
    } finally {
      setLoading(false);
    }
  }, []);

  const createProject = useCallback(async (name: string, requirements: string): Promise<string> => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/projects`, {
        name,
        requirements
      });
      const newProject = response.data;
      setProjects(prev => [...prev, newProject]);
      setCurrentProject(newProject);
      return newProject.project_id;
    } catch (err: any) {
      setError(err.message || 'Failed to create project');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const selectProject = useCallback((projectId: string) => {
    const project = projects.find(p => p.project_id === projectId);
    setCurrentProject(project || null);
  }, [projects]);

  const pauseProject = useCallback(async (projectId: string) => {
    try {
      await axios.post(`${API_BASE_URL}/api/projects/${projectId}/pause`);
      await fetchProjects();
    } catch (err: any) {
      setError(err.message || 'Failed to pause project');
      throw err;
    }
  }, [fetchProjects]);

  const resumeProject = useCallback(async (projectId: string) => {
    try {
      await axios.post(`${API_BASE_URL}/api/projects/${projectId}/resume`);
      await fetchProjects();
    } catch (err: any) {
      setError(err.message || 'Failed to resume project');
      throw err;
    }
  }, [fetchProjects]);

  const value: ProjectContextType = {
    projects,
    currentProject,
    loading,
    error,
    fetchProjects,
    createProject,
    selectProject,
    pauseProject,
    resumeProject
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}