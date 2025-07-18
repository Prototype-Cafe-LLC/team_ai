export interface Project {
  project_id: string;
  name: string;
  status: ProjectStatus;
  current_phase?: Phase;
  created_at: string;
  updated_at?: string;
}

export enum ProjectStatus {
  INITIALIZED = 'initialized',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum Phase {
  REQUIREMENTS = 'requirements',
  DESIGN = 'design',
  IMPLEMENTATION = 'implementation',
  TEST = 'test'
}

export interface PhaseInfo {
  phase: Phase;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  startedAt?: string;
  completedAt?: string;
  iterations?: number;
}

export interface Message {
  id: string;
  type: 'agent_output' | 'system' | 'error' | 'phase_transition';
  content: string;
  agent_id?: string;
  timestamp: Date;
  metadata?: any;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  content?: string;
  agent_id?: string;
  to_phase?: string;
  message?: string;
}