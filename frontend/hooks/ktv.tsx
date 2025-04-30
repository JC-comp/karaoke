"use client";

import { useRouter } from 'next/navigation';

export function useRoomID({ encodedRoomID }: { encodedRoomID: string | null }) {
  const router = useRouter();
  const roomID = encodedRoomID ? atob(encodedRoomID) : null;
  const setRoomID = (newRoomID: string | null) => {
    if (newRoomID) {
      if (newRoomID !== roomID) {
        router.push(`?roomID=${btoa(newRoomID)}`);
      }
    }
  }


  return { roomID, setRoomID };
}