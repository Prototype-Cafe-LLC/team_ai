import React from 'react';
import { Provider } from 'react-redux';
import styles from './App.module.css';
import { store } from './store/store';
import ProjectPanel from './components/ProjectPanel/ProjectPanel';
import PhaseProgress from './components/PhaseProgress/PhaseProgress';
import ActivityStream from './components/ActivityStream/ActivityStream';
import ProjectForm from './components/ProjectForm/ProjectForm';
import { ToastProvider } from './components/Toast/Toast';

function App() {
  return (
    <Provider store={store}>
      <ToastProvider>
        <div className={styles.container}>
          <header className={styles.header}>
            <div className={styles.headerContent}>
              <h1 className={styles.title}>Multi-Agent Development System</h1>
            </div>
          </header>
          
          <main className={styles.mainContent}>
            <aside className={styles.sidebar}>
              <ProjectPanel />
            </aside>
            
            <div className={styles.contentArea}>
              <ProjectForm />
              <PhaseProgress />
              <ActivityStream />
            </div>
          </main>
        </div>
      </ToastProvider>
    </Provider>
  );
}

export default App;
