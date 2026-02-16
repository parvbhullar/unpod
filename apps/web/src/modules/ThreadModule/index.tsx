'use client';
import { Fragment, useState } from 'react';
import dynamic from 'next/dynamic';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import PageHeader from './PageHeader';
import { AgentConnectionProvider } from '@unpod/livekit/hooks/useAgentConnection';
import type { Thread } from '@unpod/constants/types';

const AppPost = dynamic(() => import('@unpod/modules/AppPost'), { ssr: false });

type ThreadModuleProps = {
  token?: string;
  post: Thread;
};

const ThreadModule = ({ token, post }: ThreadModuleProps) => {
  console.log('post', post);
  const [currentPost, setCurrentPost] = useState<Thread | null>(post);

  return (
    <Fragment>
      <PageHeader currentPost={currentPost} setCurrentPost={setCurrentPost} />

      <AppPageContainer>
        {currentPost ? (
          <AgentConnectionProvider>
            <AppPost token={token} currentPost={currentPost} />
          </AgentConnectionProvider>
        ) : null}
      </AppPageContainer>
    </Fragment>
  );
};

export default ThreadModule;
