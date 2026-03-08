type Action<T> =
    | { type: 'START_SEARCH'; query: string }
    | { type: 'SET_RESULTS'; data: T[] }
    | { type: 'SET_ERROR'; error: string }
    | { type: 'CLEAR' };

type SearchState<T> =
    | { status: 'idle'; data: [] }
    | { status: 'loading'; data: T[] }
    | { status: 'success'; data: T[] }
    | { status: 'error'; data: []; error: string };

interface SearchResult {
    channel: string,
    duration: string,
    id: string,
    long_desc: string,
    publish_time: string,
    thumbnail: string,
    title: string,
    url_suffix: string,
    viewCountText: string
}