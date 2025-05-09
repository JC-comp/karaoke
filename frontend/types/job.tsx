interface Metadata {
  channel: string;
  title: string;
  id: string;
  duration: number;
}

interface Media {
  source: string;
  metadata: Metadata;
}

type JobType = 'youtube' | 'local';
type JobStatus = 'pending' | 'queued' | 'created' | 'running' | 'interrupting' | 'interrupted' | 'completed' | 'failed' | 'canceled';

interface JobInfo {
  jid: string;
  created_at: number;
  started_at: number | null;
  finished_at: number | null;
  type: JobType;
  media: Media;
  status: JobStatus;
  message: string;
  isProcessExited: boolean;
  tasks: { [key: string]: Task };
  artifact_tags: Record<string, number>;
  isRunning: () => boolean;
}