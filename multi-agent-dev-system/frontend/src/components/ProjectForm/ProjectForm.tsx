import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import * as Dialog from '@radix-ui/react-dialog';
import * as Label from '@radix-ui/react-label';
import styles from './ProjectForm.module.css';
import { createProjectRequest } from '../../store/slices/projectSlice';
import { RootState, AppDispatch } from '../../store/store';

const ProjectForm: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { loading, error } = useSelector((state: RootState) => state.project);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [requirements, setRequirements] = useState('');
  const [formError, setFormError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!name.trim()) {
      setFormError('Project name is required');
      return;
    }

    if (!requirements.trim()) {
      setFormError('Requirements are required');
      return;
    }

    dispatch(createProjectRequest({ name, requirements }));
    
    // Reset form and close dialog on success
    if (!error) {
      setName('');
      setRequirements('');
      setOpen(false);
    }
  };

  const handleCancel = () => {
    setName('');
    setRequirements('');
    setFormError('');
    setOpen(false);
  };

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <div className={styles.container}>
        <h2 className={styles.title}>Create New Project</h2>
        <Dialog.Trigger asChild>
          <button className={styles.primaryButton}>
            Start New Project
          </button>
        </Dialog.Trigger>
      </div>

      <Dialog.Portal>
        <Dialog.Overlay style={{
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          position: 'fixed',
          inset: 0,
          zIndex: 40
        }} />
        <Dialog.Content style={{
          backgroundColor: '#111111',
          borderRadius: '8px',
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '90vw',
          maxWidth: '500px',
          maxHeight: '85vh',
          padding: '2rem',
          zIndex: 50
        }}>
          <Dialog.Title style={{
            fontSize: '1.5rem',
            marginBottom: '1.5rem',
            color: '#ffffff'
          }}>
            Create New Project
          </Dialog.Title>
          
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.fieldGroup}>
              <Label.Root className={styles.label} htmlFor="name">
                Project Name
              </Label.Root>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={styles.input}
                placeholder="My Awesome Project"
                disabled={loading}
              />
            </div>

            <div className={styles.fieldGroup}>
              <Label.Root className={styles.label} htmlFor="requirements">
                Requirements
              </Label.Root>
              <textarea
                id="requirements"
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                className={styles.textarea}
                placeholder="Describe what you want to build..."
                disabled={loading}
              />
            </div>

            {(formError || error) && (
              <div className={styles.error}>
                {formError || error}
              </div>
            )}

            <div className={styles.buttonGroup}>
              <button
                type="submit"
                className={styles.primaryButton}
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Project'}
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className={styles.secondaryButton}
                disabled={loading}
              >
                Cancel
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default ProjectForm;