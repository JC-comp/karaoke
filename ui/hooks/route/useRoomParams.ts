'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useMemo } from 'react';

export default function useRoomNavigation() {
  const router = useRouter();
  const searchParams = useSearchParams();

  /**
   * 1. EXTRACT & DECODE
   * Reads ?roomID=... from URL and decodes it for the app.
   */
  const roomID = useMemo(() => {
    const encoded = searchParams.get('roomID');
    if (!encoded) return null;

    try {
      // Use atob to decode the Base64 from the URL back to text
      return atob(encoded);
    } catch (e) {
      console.error("Invalid roomID encoding in URL");
      return null;
    }
  }, [searchParams]);

  /**
   * 2. ENCODE & NAVIGATE
   * Takes a plain text room name, encodes it, and updates the URL.
   */
  const navigateToRoom = useCallback((roomName: string) => {
    if (!roomName) return;

    // Prevent redundant navigation if we are already in that room
    if (roomName !== roomID) {
      const encoded = btoa(roomName);
      router.push(`?roomID=${encoded}`);
    }
  }, [router, roomID]);

  const { roomURL, controlURL } = useMemo(() => {
    const encoded = roomID ? btoa(roomID) : '';
    const query = `?roomID=${encoded}`;

    return {
      roomURL: `/ktv${query}`,
      controlURL: `/${query}`
    };
  }, [roomID]);

  const toggleURL = useCallback(() => {
    if (!roomID) return;
    if (window.location.pathname === '/ktv') {
      router.push(controlURL);
    } else {
      router.push(roomURL);
    }
  }, [roomID, router, roomURL, controlURL]);

  return { roomID, navigateToRoom, roomURL, controlURL, toggleURL };
}