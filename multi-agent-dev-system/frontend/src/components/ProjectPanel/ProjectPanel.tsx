import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import clsx from 'clsx';
import styles from './ProjectPanel.module.css';
import { RootState, AppDispatch } from '../../store/store';
import {
  fetchProjectsRequest,
  selectProject,
  pauseProjectRequest,
  resumeProjectRequest
} from '../../store/slices/projectSlice';
import { connectWebSocket, disconnectWebSocket } from '../../store/slices/webSocketSlice';
import { ProjectStatus } from '../../store/types';

const ProjectPanel: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { projects, currentProject, loading } = useSelector((state: RootState) => state.project);
  const { connected, projectId: connectedProjectId } = useSelector((state: RootState) => state.webSocket);

  useEffect(() => {
    // Fetch projects on mount
    dispatch(fetchProjectsRequest());
  }, [dispatch]);

  const handleSelectProject = (projectId: string) => {
    dispatch(selectProject(projectId));
  };

  const handleConnectWebSocket = (projectId: string) => {
    if (connected && connectedProjectId === projectId) {
      dispatch(disconnectWebSocket());
    } else {
      if (connected) {
        dispatch(disconnectWebSocket());
      }
      dispatch(connectWebSocket(projectId));
    }
  };

  const handlePauseProject = (projectId: string) => {
    dispatch(pauseProjectRequest(projectId));
  };

  const handleResumeProject = (projectId: string) => {
    dispatch(resumeProjectRequest({ projectId }));
  };

  const handleRefresh = () => {
    dispatch(fetchProjectsRequest());
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case ProjectStatus.RUNNING:
        return styles.statusRunning;
      case ProjectStatus.PAUSED:
        return styles.statusPaused;
      case ProjectStatus.COMPLETED:
        return styles.statusCompleted;
      case ProjectStatus.FAILED:
        return styles.statusFailed;
      default:
        return styles.statusBadge;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className={styles.container}>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Projects</h3>
        
        {projects.length === 0 ? (
          <div className={styles.emptyState}>
            No projects yet
          </div>
        ) : (
          <div className={styles.projectList}>
            {projects.map(project => (
              <div
                key={project.project_id}
                className={clsx(
                  styles.projectItem,
                  currentProject?.project_id === project.project_id && styles.projectItemActive
                )}
                onClick={() => handleSelectProject(project.project_id)}
              >
                <div className={styles.projectName}>{project.name}</div>
                <div className={styles.projectMeta}>
                  <div className={getStatusClass(project.status)}>
                    <span className={styles.statusDot} />
                    {project.status}
                  </div>
                  <span>{formatDate(project.created_at)}</span>
                </div>
                
                {currentProject?.project_id === project.project_id && (
                  <div className={styles.controls}>
                    <button
                      className={styles.connectButton}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleConnectWebSocket(project.project_id);
                      }}
                    >
                      {connected && connectedProjectId === project.project_id
                        ? 'Disconnect'
                        : 'Connect WebSocket'}
                    </button>
                    
                    {project.status === ProjectStatus.RUNNING && (
                      <button
                        className={styles.pauseButton}
                        onClick={(e) => {
                          e.stopPropagation();
                          handlePauseProject(project.project_id);
                        }}
                      >
                        Pause
                      </button>
                    )}
                    
                    {project.status === ProjectStatus.PAUSED && (
                      <button
                        className={styles.resumeButton}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleResumeProject(project.project_id);
                        }}
                      >
                        Resume
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        <button
          className={styles.refreshButton}
          onClick={handleRefresh}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh Projects'}
        </button>
      </div>
    </div>
  );
};

export default ProjectPanel;