import React, { useState, useEffect } from 'react';
import { useDebounce } from 'react-use';

export function useSearchYoutubeKeywordSuggestion() {
    const [query, setQuery] = useState('');
    const [debouncedQuery, setDebouncedQuery] = React.useState('');
    useDebounce(
        () => {
            setDebouncedQuery(query);
        },
        500,
        [query]
    );


    const [suggestions, setSuggestions] = useState([]);

    // Fetch suggestions when debouncedQuery changes
    useEffect(() => {
        if (debouncedQuery.length == 0) {
            setSuggestions([]);
            return;
        }
        const controller = new AbortController();
        fetch('/api/youtube/keyword?q=' + encodeURIComponent(debouncedQuery), {
            signal: controller.signal,
        })
            .then((res) => res.json())
            .then((data) => {
                if (!data.success)
                    throw new Error(data.message);
                const result = data.body;
                setSuggestions(result.options);
            })
            .catch((err) => {
                if (err.name === 'AbortError')
                    return;
                setSuggestions([]);
            });
        return () => {
            controller.abort();
        }
    }, [debouncedQuery]);

    return {
        query, setQuery, suggestions
    }
}