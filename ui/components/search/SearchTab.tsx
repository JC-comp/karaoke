import React, { useEffect, useRef, useState } from 'react';
import { useClickAway } from 'react-use';
import { useSearchYoutubeKeywordSuggestion } from '@/hooks/search/useSearchKeyword';
import styles from './SearchTab.module.css';
import { useSearchYoutubeQuery } from '@/hooks/search/useSearchQuery';
import SearchResult from './SearchResult';

export default function SearchTab({ isActive }: TabProps) {
  const { query: keyword, setQuery: setKeyword, suggestions } = useSearchYoutubeKeywordSuggestion();
  const { setQuery, state } = useSearchYoutubeQuery();
  const inputContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useClickAway(inputContainerRef, () => setShowDropdown(false));

  const performQuery = (query: string) => {
    setKeyword(query);
    setQuery(query);
    setShowDropdown(false);
  }

  useEffect(() => {
    if (isActive) {
      inputRef.current?.focus();
    }
  }, [isActive]);

  return (
    <div className={`${styles.holder} d-flex flex-column`}>
      <div ref={inputContainerRef}>
        <input ref={inputRef} id='keyword' type="text" className={`${styles.queryBox} form-control`} placeholder="Search keywords" value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onFocus={(e) => setShowDropdown(true)}
        />
        {
          showDropdown && suggestions.length > 0 && <div className={styles.suggestionHolder}>
            {
              suggestions.map((option, index) => (
                <div key={index} className={`${styles.suggestion} rounded`} onClick={() => performQuery(option)}>
                  <span>{option}</span>
                </div>
              ))
            }
          </div>
        }
      </div>
      <SearchResult state={state} />
    </div>
  );
}