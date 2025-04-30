interface LogLine {
  timestamp: string;
  pid: string;
  module: string;
  level: string;
  message: string;
}

interface Artifact {
  aid: string;
  name: string;
  artifact_type: 'video' | 'audio' | 'json' | 'text' | 'segments';
  is_attached: boolean;
}

type TaskStatus = 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'soft_failed' | 'canceled' | 'skipped' | 'interrupting' | 'interrupted';

interface Task {
  tid: string;
  name: string;
  status: TaskStatus;
  message: string;
  output: string;
  artifacts: Artifact[];
  hasArtifact: () => boolean;
}
