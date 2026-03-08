'use client';

import { ComponentType, useEffect, useState } from 'react';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';

import ThemeToggler from '@/components/theme/ThemeToggler';
import SearchTab from '@/components/search/SearchTab';
import styles from "./page.module.css"
import KareokeRoom from '@/components/room/KareokeRoom';
import ProgressTab from '@/components/progress/ProgressTab';
import { useKTVRoom } from '@/hooks/room/useKTVRoom';
import useTabNavigation from '@/hooks/useTabNavigation';

type TabKey = 'search' | 'youtube' | 'file' | 'progress';

interface TabConfig {
  title: string;
  enabled: boolean;
  persist: boolean;
  component: React.ComponentType<TabProps>;
}

const TAB_INFO: Record<TabKey, TabConfig> = {
  search: {
    title: 'Search',
    enabled: true,
    persist: true,
    component: SearchTab
  },
  youtube: {
    title: 'YouTube Link',
    enabled: false,
    persist: false,
    component: () => <></>
  },
  file: {
    title: 'Local file',
    enabled: false,
    persist: false,
    component: () => <></>
  },
  progress: {
    title: 'Progress',
    enabled: true,
    persist: false,
    component: ProgressTab
  }
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>('search');
  const { roomModel } = useKTVRoom();
  const { navigateToTab } = useTabNavigation(setActiveTab)

  useEffect(() => {
    if (activeTab === 'search') {
      
    }
  }, [activeTab])

  return (
    <div className="root flex-column">
      <ThemeToggler />
      <h1 className="mb-4 text-primary">Welcome to JTV!</h1>
      <div className={styles.main}>
        <KareokeRoom room={roomModel} />
        <div>
          <Tabs className="mb-3" activeKey={activeTab} onSelect={(k) => navigateToTab(k || 'search')}>
            {
              Object.entries(TAB_INFO).filter(([key, value]) => value.enabled)
                .map(([key, value]) => {
                  const TabComponent = value.component;
                  return (
                    <Tab
                      eventKey={key} title={value.title} key={key}
                      unmountOnExit={!value.persist} mountOnEnter={true}>
                      {
                        <TabComponent isActive={activeTab === key} />
                      }
                    </Tab>
                  )
                })
            }
          </Tabs>
        </div>
      </div>
    </div>
  );
}