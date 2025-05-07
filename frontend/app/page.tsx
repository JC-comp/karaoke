'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'next/navigation'
import { SearchJobTab, YoutubeJobTab, FileJobTab, ProgressTab } from '@/components/Tabs';
import KareokeRoom from '@/components/ktv/KareokeRoom';
import KareokeRoomModel from '@/models/ktv';
import { useRoomID } from '@/hooks/ktv';
import styles from "./page.module.css"
import "@/components/tabs/SearchJobTab.css";
import "@/components/tabs/Tab.css"
import "@/components/ktv/KareokeRoom.css";

const TAB_INFO = {
  search: {
    title: 'Search'
  },
  youtube: {
    title: 'YouTube Link'
  },
  file: {
    title: 'Local file'
  },
  progress: {
    title: 'Progress'
  }
}

export default function Home() {
  const searchParams = useSearchParams()
  const formRef = useRef<HTMLFormElement>(null);
  const [activeTab, setActiveTab] = useState<string>('search');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isShowing, setIsShowing] = useState<boolean>(true);
  const encodedRoomID = searchParams.get('roomID');
  const [kareokeRoomModel, setKareokeRoomModel] = useState<KareokeRoomModel | null>(null);
  const { roomID, setRoomID } = useRoomID({ encodedRoomID });
  const [version, setVersion] = useState<number>(0);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    setIsShowing(false);
    window.location.hash = `#${tab}`;
    setTimeout(() => {
      setIsShowing(true);
    }, 100); // Adjust the timeout to match your desired transition duration
  };

  useEffect(() => {
    const hashchange = () => {
      const hash = window.location.hash;
      if (!hash) return;
      if (hash === '#search') {
        setActiveTab('search');
      }
    }
    window.addEventListener('hashchange', hashchange);
    return () => {
      window.removeEventListener('hashchange', hashchange);
    }
  }, []);

  return (
    <div className="root flex-column">
      <h1 className="mb-4 text-primary">Welcome to JTV!</h1>
      <div className={styles.main}>
        <KareokeRoom kareokeRoomModel={kareokeRoomModel} setKareokeRoomModel={setKareokeRoomModel} roomID={roomID} setRoomID={setRoomID} version={version} setVersion={setVersion}  />
        <div className={`${styles["action-panel"]} d-flex flex-column shadow rounded`}>
          {/* Tab Navigation */}
          <ul className="nav nav-tabs mb-1 flex-nowrap text-nowrap overflow-x-auto overflow-y-hidden">
            {
              Object.entries(TAB_INFO).map(([tab, { title }]) => (
                <li className="nav-item" key={tab} style={{ cursor: isProcessing ? 'not-allowed' : 'pointer' }}>
                  <button
                    className={`nav-link ${activeTab === tab ? 'active' : ''}`}
                    onClick={() => handleTabChange(tab)}
                    disabled={isProcessing}
                  >
                    {title}
                  </button>
                </li>
              ))
            }
          </ul>

          {/* Tab Content */}
          <div className='position-relative'>
            <form ref={formRef} onSubmit={(e) => { e.preventDefault(); }}>
              <div className={`tab-pane fade active ${isShowing ? 'show' : ''}`} style={ isShowing ? {} : { height: '0', overflow: 'hidden' }}>
                <SearchJobTab activeTab={activeTab} roomID={roomID} />
                {
                  activeTab === 'youtube' && <YoutubeJobTab setIsProcessing={setIsProcessing} isProcessing={isProcessing} />
                }
                {
                  activeTab === 'file' && <FileJobTab setIsProcessing={setIsProcessing} isProcessing={isProcessing} />
                }
                {
                  activeTab === 'progress' && <ProgressTab />
                }
              </div>
            </form>
            {
              isProcessing && <div className="position-absolute w-100 h-100 top-0 start-0"
                style={{ cursor: 'wait' }}>
              </div>
            }
          </div>
        </div>
      </div>
    </div>
  );
}