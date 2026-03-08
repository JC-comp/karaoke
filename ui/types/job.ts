type JobType = 'youtube' | 'local';
type JobStatus = 'queued' | 'running' | 'success' | 'failed' | 'none';
type ArtifactKey = 'metadata' | 'Instrumental' | 'subtitles';
interface ArtifactTag {
  type: 'json' | 'file';
  value: any;
}
interface SourceTag {
  value: any;
}
