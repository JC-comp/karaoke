import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ToastContentProps, toast } from 'react-toastify';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
import { submitJob } from '@/utils/job';

const AddConfirmation = ({ closeToast, data }: ToastContentProps<{ add: () => void }>) => {
  return (
    <div className="d-flex flex-column flex-grow-1">
      <div>
        Video already added to queue.
      </div>
      <button className="btn btn-danger btn-sm mt-2 align-self-end"
        onClick={() => {
          closeToast();
          data.add();
        }}
      >
        Add anyway
      </button>
    </div>
  );
};

enum PlaylistItemType {
  YOUTUBE = 'YoutubePlaylistItem',
  SCHEDULE = 'SchedulePlaylistItem',
}

const QueueButton = ({ roomID, body, isProcessing, setIsProcessing, text }: { roomID: string | null, body: BodyInit | null, isProcessing: boolean, setIsProcessing: (isProcessing: boolean) => void; text: string }) => {
  const [isQueued, setIsQueued] = useState<boolean>(false);

  useEffect(() => {
    if (!body) return;
    if (isQueued) {
      setIsProcessing(false);
      toast.warning(AddConfirmation, {
        data: {
          add: () => {
            setIsQueued(false);
            setIsProcessing(true);
          }
        }
      });
      return;
    }
    const controller = new AbortController();
    if (!roomID) {
      toast.error('Kareoke room is still loading.');
      setIsProcessing(false);
      return;
    }
    fetch('/api/ktv/queue', {
      method: 'POST',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
      body: body
    }).then((res) => {
      return res.json().catch(() => {
        throw new Error(`${res.status}: ${res.statusText}`);
      });
    }).then((data) => {
      if (!data.success) {
        throw new Error(data.message);
      }
      setIsQueued(true);
    }).catch((err) => {
      if (err.name === 'AbortError') {
        return;
      }
      toast.error(`An error occurred while queuing the video. (${err.message})`);
    }).finally(() => {
      setIsProcessing(false);
    })

    return () => {
      controller.abort();
    }
  }, [body]);

  useEffect(() => {
    setIsQueued(false);
    setIsProcessing(false);
  }, [roomID]);

  return <button className={`btn ${isQueued ? 'btn-success' : 'btn-secondary'} me-2`}
    onClick={() => setIsProcessing(true)}
    disabled={isProcessing}
  >
    {
      isProcessing ? <FontAwesomeIcon icon={faSpinner} spin />
        : isQueued ? 'Queued' : text
    }
  </button>
}

const QueueYoutubeButton = ({ roomID, searchResult }: { roomID: string | null, searchResult: VideoResult }) => {
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [body, setBody] = useState<BodyInit | null>(null);

  useEffect(() => {
    if (!isProcessing) return;
    setBody(JSON.stringify({
      room_id: roomID,
      item_type: PlaylistItemType.YOUTUBE,
      item: searchResult
    })
    )

    return () => {
      setBody(null);
    }
  }, [isProcessing]);

  return <QueueButton
    roomID={roomID} body={body}
    isProcessing={isProcessing} setIsProcessing={setIsProcessing}
    text='Queue'
  />
}

const QueueScheduleButton = ({ roomID, searchResult }: { roomID: string | null, searchResult: VideoResult }) => {
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [body, setBody] = useState<BodyInit | null>(null);

  useEffect(() => {
    if (!isProcessing) return;
    if (!jobId) return;
    setBody(JSON.stringify({
      room_id: roomID,
      item_type: PlaylistItemType.SCHEDULE,
      item: {
        ...searchResult,
        job_id: jobId
      }
    }))
    
    return () => {
      setBody(null);
    }
  }, [jobId, isProcessing]);

  useEffect(() => {
    if (!isProcessing) return;
    if (jobId) return;
    const formData = new FormData();
    formData.append('youtubeLink', `https://youtube.com${searchResult.url_suffix}`);

    submitJob(formData)
      .then((jobId) => {
        setJobId(jobId);
      })
      .catch((err) => {
        toast.error(`An error occurred while queuing the video. (${err.message})`);
        setIsProcessing(false);
      });

  }, [isProcessing]);

  return <QueueButton
    roomID={roomID} body={body}
    isProcessing={isProcessing} setIsProcessing={setIsProcessing}
    text='Convert&Queue'
  />
}

export default function SearchJobTab({ activeTab, roomID }: { activeTab: string, roomID: string | null }) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [keyword, setKeyword] = useState<string>('');
  const [keywordOptions, setKeywordOptions] = useState<string[]>([]);
  const [showKeywordOptions, setShowKeywordOptions] = useState<boolean>(true);
  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [searchRequested, setSearchRequested] = useState<boolean>(false);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchResults, setSearchResults] = useState<VideoResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (keyword.length == 0) {
      setKeywordOptions([]);
      return;
    } else {

      fetch('/api/youtube/keyword?q=' + encodeURIComponent(keyword))
        .then((res) => res.json())
        .then((data) => {
          if (!data.success)
            throw new Error(data.message);
          const result = data.body;
          if (result.keyword == keyword)
            setKeywordOptions(result.options);
        })
        .catch((err) => {
          console.log(err);
        });
    }
  }, [keyword]);

  useEffect(() => {
    if (searchKeyword.length == 0)
      return;
    setIsSearching(true);
    setError(null);
    const controller = new AbortController();
    fetch('/api/youtube/search?q=' + encodeURIComponent(searchKeyword), {
      signal: controller.signal,
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data.success)
          throw new Error(data.message);
        const result = data.body;
        if (result.keyword == searchKeyword) {
          setSearchResults(result.results);
          setIsSearching(false);
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') {
          console.log('Fetch aborted');
          return;
        }
        console.log(err);
        setError('An error occurred while searching.');
      });

    return () => {
      controller.abort();
    }
  }, [searchKeyword]);

  const showKeywordPanel = () => {
    setShowKeywordOptions(true);
    setSearchRequested(false);
  }

  const hideKeywordPanel = () => {
    setShowKeywordOptions(false);
  }

  return <div className={`searchHolder ${activeTab === 'search' ? '' : 'd-none'}`}>
    <div className="searchbox d-flex flex-column">
      <input id="search" type="text" className="form-control" placeholder="Search keywords" value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        onFocus={(e) => showKeywordPanel()}
        onBlur={(e) => hideKeywordPanel()}
      />
      {
        keywordOptions.length > 0 && !searchRequested && <div ref={inputRef} className={`options flex-column ${showKeywordOptions ? 'show' : ''}`}>
          {
            keywordOptions.map((option, index) => (
              <div key={index} className="rounded" onClick={() => {
                setKeyword(option);
                setSearchKeyword(option);
                setSearchRequested(true);
                hideKeywordPanel();
              }}>
                <span>{option}</span>
              </div>
            ))
          }
        </div>
      }
    </div>
    <div className="d-flex justify-content-center flex-column align-items-center">
      {
        error && <div className="alert alert-danger w-100" role="alert">
          {error}
        </div>
      }
      {
        !error && isSearching && <div className='mt-3'>
          <FontAwesomeIcon icon={faSpinner} className="fa-spin" />
        </div>
      }
      {
        !error && searchResults.length > 0 && searchResults.map((result) => (
          <div key={result.id} className="result-wrapper rounded">
            <div className="result-item">
              <div className="thumbnail">
                <img className='rounded' src={result.thumbnail} alt="Track Thumbnail" />
              </div>
              <div className="track-info">
                <h5 className="track-title">
                  <Link href={`https://youtube.com${result.url_suffix}`} target='_blank' rel="noopener noreferrer">
                    {result.title}
                  </Link>
                </h5>
                <p className="artist-name text-truncate">{result.channel}</p>
                <span className="track-description">{result.long_desc}</span>
              </div>
            </div>
            <div className="text-end">
              <QueueScheduleButton roomID={roomID} searchResult={result} />
              <QueueYoutubeButton roomID={roomID} searchResult={result} />
            </div>
          </div>
        ))
      }
    </div>
  </div>
}