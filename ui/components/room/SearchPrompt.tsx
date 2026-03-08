import useTabNavigation from '@/hooks/useTabNavigation';

export default function SearchPrompt() {
      const { navigateToTab } = useTabNavigation();
    return <>
        , please add songs with the <button type='button' className='btn btn-link p-0 m-0 align-baseline' onClick={() => navigateToTab('search')}>search tab</button>
    </>;
}