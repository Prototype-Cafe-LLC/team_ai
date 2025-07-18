import React from 'react';
import { useSelector } from 'react-redux';
import clsx from 'clsx';
import styles from './PhaseProgress.module.css';
import { RootState } from '../../store/store';
import { Phase } from '../../store/types';

interface PhaseInfo {
  name: string;
  phase: Phase;
  icon: string;
}

const phases: PhaseInfo[] = [
  { name: 'Requirements', phase: Phase.REQUIREMENTS, icon: '📋' },
  { name: 'Design', phase: Phase.DESIGN, icon: '🎨' },
  { name: 'Implementation', phase: Phase.IMPLEMENTATION, icon: '💻' },
  { name: 'Test', phase: Phase.TEST, icon: '🧪' }
];

const PhaseProgress: React.FC = () => {
  const currentProject = useSelector((state: RootState) => state.project.currentProject);

  const getPhaseStatus = (phase: Phase) => {
    if (!currentProject) return 'pending';
    
    const currentPhaseIndex = phases.findIndex(p => p.phase === currentProject.current_phase);
    const phaseIndex = phases.findIndex(p => p.phase === phase);
    
    if (currentProject.status === 'completed' && phaseIndex <= currentPhaseIndex) {
      return 'completed';
    }
    
    if (currentProject.current_phase === phase && currentProject.status === 'running') {
      return 'active';
    }
    
    if (phaseIndex < currentPhaseIndex) {
      return 'completed';
    }
    
    return 'pending';
  };

  const getPhaseClass = (status: string) => {
    switch (status) {
      case 'active':
        return styles.phaseActive;
      case 'completed':
        return styles.phaseCompleted;
      case 'failed':
        return styles.phaseFailed;
      default:
        return styles.phasePending;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'In Progress';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return 'Pending';
    }
  };

  if (!currentProject) {
    return (
      <div className={styles.container}>
        <h2 className={styles.title}>Project Progress</h2>
        <div style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>
          No project selected. Create or select a project to see progress.
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Project Progress</h2>
      <div className={styles.phases}>
        {phases.map((phaseInfo, index) => {
          const status = getPhaseStatus(phaseInfo.phase);
          const isLast = index === phases.length - 1;
          
          return (
            <div key={phaseInfo.phase} style={{ position: 'relative' }}>
              <div className={getPhaseClass(status)}>
                <div className={styles.phaseIcon}>{phaseInfo.icon}</div>
                <div className={styles.phaseName}>{phaseInfo.name}</div>
                <div className={styles.phaseStatus}>{getStatusText(status)}</div>
                
                {status === 'active' && (
                  <div className={styles.progressBar}>
                    <div 
                      className={styles.progressFill}
                      style={{ width: '50%' }}
                    />
                  </div>
                )}
              </div>
              
              {!isLast && (
                <div 
                  className={clsx(
                    styles.connector,
                    status === 'completed' && styles.connectorActive
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PhaseProgress;