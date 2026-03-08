export class TaskInfo {
    jid: string = "";
    tid: string = "";
    name: string = "";
    status: TaskStatus = 'none';
    artifacts: Record<string, Artifact> = {};
    output: Record<string, any>[] = [];

    public applyUpdate(data: Partial<TaskInfo>) {
        Object.assign(this, data);
        this.status = this.status ?? 'none';
    }

    hasArtifact(): boolean {
        return Object.values(this.artifacts).filter(artifact => artifact.attached).length > 0;
    }
}