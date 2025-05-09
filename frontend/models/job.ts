import { Task } from "./task";

export class JobInfo {
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
    constructor(jid: string, created_at: number, started_at: number | null, finished_at: number | null, type: JobType, media: Media, status: JobStatus, message: string, isProcessExited: boolean, artifact_tags: Record<string, number>, tasks: { [key: string]: Task }) {
        this.jid = jid;
        this.created_at = created_at;
        this.started_at = started_at;
        this.finished_at = finished_at;
        this.type = type;
        this.media = media;
        this.status = status;
        this.message = message;
        this.isProcessExited = isProcessExited;
        this.artifact_tags = artifact_tags;
        this.tasks = tasks;
    }

    isRunning(): boolean {
        switch (this.status) {
            case 'pending':
            case 'queued':
            case 'created':
            case 'running':
                return true;
            case 'interrupting':
            case 'interrupted':
            case 'completed':
            case 'failed':
            case 'canceled':
                return false;
        }
    }


    static fromJSON(json: any): JobInfo {
        return new JobInfo(
            json.jid,
            json.created_at,
            json.started_at,
            json.finished_at,
            json.type,
            json.media,
            json.status,
            json.message,
            json.isProcessExited,
            json.artifact_tags,
            Object.fromEntries(
                Object.entries(json.tasks).map(([key, value]) => [key, Task.fromJSON(value)])
            )
        );
    }
}