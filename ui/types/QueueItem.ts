export type QueueItem = {
  id: string,
  title: string,
  channel: string
} | {
  id: string,
  title: string,
  artist: string
}

export type QueueItemType = 'youtube' | 'job';

export interface QueuePayload {
  item_type: QueueItemType,
  item: QueueItem
}
