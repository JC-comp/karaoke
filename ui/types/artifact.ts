interface Artifact {
    name: string;
    type: 'json' | 'text' | 'audio' | 'segment' | 'sentence';
    attached: boolean;
    is_artifact: boolean;
    value: any;
}
