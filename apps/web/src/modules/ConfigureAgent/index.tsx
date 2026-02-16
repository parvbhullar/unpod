'use client';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import React from 'react';
import { StyledMainContent, StyledRoot } from './index.styled';
import dynamic from 'next/dynamic';
import AppModuleContextProvider from '@unpod/providers/AppModuleContextProvider';

type ConfigureAgentProps = Record<string, unknown>;

const AppAgentModule = dynamic<any>(
  () => import('@unpod/modules/AppAgentModule'),
  { ssr: false },
);

const ConfigureAgent: React.FC<ConfigureAgentProps> = (props) => {
  return (
    <AppModuleContextProvider type="agent">
      <AppPageContainer>
        <StyledRoot>
          <StyledMainContent>
            <AppAgentModule {...props} />
          </StyledMainContent>
        </StyledRoot>
      </AppPageContainer>
    </AppModuleContextProvider>
  );
};

export default ConfigureAgent;
