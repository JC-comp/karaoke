import { useState, useEffect, useReducer } from 'react';

const searchReducer = (state: SearchState<SearchResult>, action: Action<SearchResult>): SearchState<SearchResult> => {
    switch (action.type) {
        case 'START_SEARCH':
            return { ...state, status: 'loading' };
        case 'SET_RESULTS':
            return { status: 'success', data: action.data };
        case 'SET_ERROR':
            return { status: 'error', data: [], error: action.error };
        case 'CLEAR':
            return { status: 'idle', data: [] };
        default:
            return state;
    }
};

export function useSearchYoutubeQuery() {
    const [query, setQuery] = useState('');
    const [state, dispatch] = useReducer(searchReducer, {
        status: 'idle',
        data: []
    });

    useEffect(() => {
        if (!query.trim()) {
            dispatch({ type: 'CLEAR' });
            return;
        }
        dispatch({ type: 'START_SEARCH', query: query });
        const controller = new AbortController();
        fetch('/api/youtube/search?q=' + encodeURIComponent(query), {
            signal: controller.signal,
        })
            .then((res) => res.json())
            .then((data) => {
                if (!data.success)
                    throw new Error(data.message);
                const results = data.body.results;
                dispatch({ type: 'SET_RESULTS', data: results });
            })
            .catch((err) => {
                if (err.name === 'AbortError')
                    return;
                dispatch({ type: 'SET_ERROR', error: 'An error occurred while searching.' });
            });

        return () => {
            controller.abort();
        }
    }, [query]);


    return {
        query, setQuery,
        state
    };
}