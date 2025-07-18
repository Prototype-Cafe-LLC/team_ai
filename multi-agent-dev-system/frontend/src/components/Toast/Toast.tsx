import React, { createContext, useContext, useState, useCallback } from 'react';
import * as ToastPrimitive from '@radix-ui/react-toast';
import clsx from 'clsx';
import styles from './Toast.module.css';

interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

interface ToastContextType {
  showToast: (title: string, description?: string, type?: ToastMessage['type']) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((
    title: string,
    description?: string,
    type: ToastMessage['type'] = 'info'
  ) => {
    const id = Date.now().toString();
    const newToast: ToastMessage = { id, title, description, type };
    setToasts(prev => [...prev, newToast]);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(toast => toast.id !== id));
    }, 5000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      <ToastPrimitive.Provider swipeDirection="right">
        {children}
        {toasts.map(toast => (
          <ToastPrimitive.Root
            key={toast.id}
            className={clsx(styles.root, styles[toast.type])}
            open={true}
            onOpenChange={(open) => {
              if (!open) removeToast(toast.id);
            }}
          >
            <ToastPrimitive.Title className={styles.title}>
              {toast.title}
            </ToastPrimitive.Title>
            {toast.description && (
              <ToastPrimitive.Description className={styles.description}>
                {toast.description}
              </ToastPrimitive.Description>
            )}
            <ToastPrimitive.Action
              className={styles.action}
              asChild
              altText="Close"
            >
              <button className={styles.closeButton}>×</button>
            </ToastPrimitive.Action>
          </ToastPrimitive.Root>
        ))}
        <ToastPrimitive.Viewport className={styles.viewport} />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
};