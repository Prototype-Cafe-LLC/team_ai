import React, { useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import * as ScrollArea from '@radix-ui/react-scroll-area';
import clsx from 'clsx';
import styles from './ActivityStream.module.css';
import { RootState, AppDispatch } from '../../store/store';
import { clearMessages } from '../../store/slices/webSocketSlice';
import { Message } from '../../store/types';

const ActivityStream: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const messages = useSelector((state: RootState) => state.webSocket.messages);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const lastMessageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleClearMessages = () => {
    dispatch(clearMessages());
  };

  const formatTimestamp = (date: Date) => {
    return new Date(date).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getMessageClass = (message: Message) => {
    switch (message.type) {
      case 'agent_output':
        return styles.agentOutput;
      case 'error':
        return styles.error;
      case 'phase_transition':
        return styles.phaseTransition;
      case 'system':
      default:
        return styles.system;
    }
  };

  const formatAgentName = (agentId?: string) => {
    if (!agentId) return null;
    
    // Convert agent_id to readable format
    const parts = agentId.split('_');
    if (parts.length >= 2) {
      const phase = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
      const role = parts[1].charAt(0).toUpperCase() + parts[1].slice(1);
      return `${phase} ${role}`;
    }
    return agentId;
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Activity Stream</h2>
        <button 
          onClick={handleClearMessages} 
          className={styles.clearButton}
          disabled={messages.length === 0}
        >
          Clear Messages
        </button>
      </div>

      <ScrollArea.Root className={styles.scrollArea}>
        <ScrollArea.Viewport className={styles.scrollViewport} ref={scrollAreaRef}>
          {messages.length === 0 ? (
            <div className={styles.emptyState}>
              No messages yet. Start a project to see activity.
            </div>
          ) : (
            <div className={styles.messageList}>
              {messages.map((message, index) => (
                <div
                  key={message.id}
                  className={getMessageClass(message)}
                  ref={index === messages.length - 1 ? lastMessageRef : null}
                >
                  <div className={styles.messageHeader}>
                    <span className={styles.timestamp}>
                      [{formatTimestamp(message.timestamp)}]
                    </span>
                    {message.agent_id && (
                      <span className={styles.agentName}>
                        {formatAgentName(message.agent_id)}:
                      </span>
                    )}
                  </div>
                  <div className={styles.messageContent}>
                    {message.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar
          className="ScrollAreaScrollbar"
          orientation="vertical"
        >
          <ScrollArea.Thumb className="ScrollAreaThumb" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </div>
  );
};

export default ActivityStream;