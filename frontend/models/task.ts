export class Task {
    tid: string;
    name: string;
    status: TaskStatus;
    message: string;
    output: string;
    artifacts: Artifact[];
    constructor(tid: string, name: string, status: TaskStatus, message: string, output: string, artifacts: Artifact[]) {
        this.tid = tid;
        this.name = name;
        this.status = status;
        this.message = message;
        this.output = output;
        this.artifacts = artifacts;
    }

    hasArtifact(): boolean {
        for (const artifact of this.artifacts) {
            if (!artifact.is_attached) {
                return true;
            }
        }
        return false;
    }


    static fromJSON(json: any): Task {
        return new Task(
            json.tid,
            json.name,
            json.status,
            json.message,
            json.output,
            json.artifacts
        );
    }
}