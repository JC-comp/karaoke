export class JobInfo {
    jid: string = "";
    created_at: string = '';
    started_at: string | null = null;
    finished_at: string | null = null;
    source: Record<string, SourceTag> = {};
    status: JobStatus = 'none';
    artifact_tags: Partial<Record<ArtifactKey, ArtifactTag>> = {};
    task_order: string[] = [];

    public applyUpdate(data: Partial<JobInfo>) {
        Object.assign(this, data);
        this.status = this.status ?? 'none';
    }

    isRunning(): boolean {
        switch (this.status) {
            case 'none':
            case 'queued':
            case 'running':
                return true;
            case 'success':
            case 'failed':
                return false;
        }
    }
}