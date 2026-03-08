import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
import styles from './SearchResult.module.css';
import QueueYoutubeButton from './QueueYoutubeButton';
import QueueJobButton from './QueueJobButton';

export default function SearchResult({ state }: { state: SearchState<SearchResult> }) {
  return (
    <div className="d-flex justify-content-center flex-column align-items-center">
      {
        state.status == 'error' && <div className="alert alert-danger w-100" role="alert">
          {state.error}
        </div>
      }
      {
        state.status == 'loading' && <div className='mt-3'>
          <FontAwesomeIcon icon={faSpinner} className="fa-spin" />
        </div>
      }
      {
        (state.status == 'success' || state.status == 'loading') && state.data.map((result) => (
          <div key={result.id} className={`${styles.holder} rounded`}>
            <div className={styles.item}>
              <div className={styles.thumbnail}>
                <img className='rounded' src={result.thumbnail} alt="Track Thumbnail" />
              </div>
              <div className={styles['track-info']}>
                <h5 className={styles["track-title"]}>
                  <Link href={`https://youtube.com${result.url_suffix}`} target='_blank' rel="noopener noreferrer">
                    {result.title}
                  </Link>
                </h5>
                <p className={`${styles['artist-name']} text-truncate`}>{result.channel}</p>
                <span className={styles["track-description"]}>{result.long_desc}</span>
              </div>
            </div>
            <div className="text-end">
              <QueueJobButton searchResult={result} />
              <QueueYoutubeButton searchResult={result} />
            </div>
          </div>
        ))
      }
    </div>
  );
}
