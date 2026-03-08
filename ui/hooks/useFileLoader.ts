import { useState, useCallback } from 'react';

interface FileLoaderState {
  data: string | null;
  isLoading: boolean;
  error: string | null;
}

export const useFileLoader = () => {
  const [state, setState] = useState<FileLoaderState>({
    data: null,
    isLoading: false,
    error: null,
  });

  const loadText = useCallback(async (url: string): Promise<string | null> => {
    setState({ data: null, isLoading: true, error: null });

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const text = await response.text();
      
      setState({ data: text, isLoading: false, error: null });
      return text;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setState({ data: null, isLoading: false, error: errorMessage });
      return null;
    }
  }, []);

  return { 
    ...state, 
    loadText
  };
};