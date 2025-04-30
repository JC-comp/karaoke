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
    result_artifact_index: number;
    tasks: { [key: string]: Task };
    constructor(jid: string, created_at: number, started_at: number | null, finished_at: number | null, type: JobType, media: Media, status: JobStatus, message: string, isProcessExited: boolean, result_artifact_index: number, tasks: { [key: string]: Task }) {
        this.jid = jid;
        this.created_at = created_at;
        this.started_at = started_at;
        this.finished_at = finished_at;
        this.type = type;
        this.media = media;
        this.status = status;
        this.message = message;
        this.isProcessExited = isProcessExited;
        this.result_artifact_index = result_artifact_index;
        this.tasks = tasks;
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
            json.result_artifact_index,
            Object.fromEntries(
                Object.entries(json.tasks).map(([key, value]) => [key, Task.fromJSON(value)])
            )
        );
    }
}