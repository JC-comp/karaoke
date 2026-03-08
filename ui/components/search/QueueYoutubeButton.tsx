import React from 'react';
import QueueButton from './QueueButton';
import { QueueItemType } from '@/types/QueueItem';

export default function QueueYoutubeButton({ searchResult }: { searchResult: SearchResult }) {
  return <QueueButton
    payload={{
      item_type: 'youtube',
      item: searchResult
    }}
    text='Queue'
  />
}