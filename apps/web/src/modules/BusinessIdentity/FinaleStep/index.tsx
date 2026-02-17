'use client';
import React, { Fragment, useState } from 'react';
import { Button, Divider, Flex } from 'antd';
import { useRouter } from 'next/navigation';
import IdentityCard, { type AgentSummary } from './IdentityCard';
import dynamic from 'next/dynamic';
import AppDrawer from '@unpod/components/antd/AppDrawer';
import {
  getDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
  useTourActionsContext,
} from '@unpod/providers';
import { setOrgHeader } from '@unpod/services';
import { StyledText } from './index.styled';
import { useIntl } from 'react-intl';
import type { User } from '@unpod/constants/types';

const VoiceAgent = dynamic<any>(
  () => import('@unpod/modules/AppAgentModule/VoiceAgent'),
  { ssr: false },
);

type FinalSummaryProps = {
  agent?: AgentSummary | null;
};

const FinalSummary = ({ agent }: FinalSummaryProps) => {
  const [loading, setLoading] = useState(false);
  const infoViewActionsContext = useInfoViewActionsContext();
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);
  const router = useRouter();
  const { setActiveOrg, updateAuthUser } =
    useAuthActionsContext();
  const { startTour } = useTourActionsContext();
  const { activeOrg } = useAuthContext();
  const { formatMessage } = useIntl();

  const onComplete = () => {
    setLoading(true);
    getDataApi<User>('auth/me/', infoViewActionsContext)
      .then(({ data }) => {
        if (!data?.active_organization?.domain_handle) {
          return;
        }
        setOrgHeader(data.active_organization.domain_handle);
        updateAuthUser(data);
        setActiveOrg({ ...activeOrg, ...data.active_organization });
        startTour();

        if (process.env.productId === 'unpod.ai' && data.active_space?.slug) {
          router.replace(`/spaces/${data.active_space?.slug}/chat/`);
        } else {
          router.push(`/org`);
        }
        // router.push(`/spaces/${data.active_space?.slug}/chat/`);
      })
      .catch((response) => {
        const payload = response as { message?: string };
        infoViewActionsContext.showError(payload.message || '');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <Fragment>
      <IdentityCard agent={agent || undefined} />

      <Divider />
      <Flex justify="space-between" align="center">
        <Button
          type="primary"
          onClick={() => setIsWidgetOpen(true)}
          style={{ paddingLeft: 24, paddingRight: 24 }}
        >
          {formatMessage({ id: 'common.talkToAgent' })}
        </Button>

        <Button
          loading={loading}
          type="primary"
          style={{ paddingLeft: 24, paddingRight: 24 }}
          onClick={() => {
            onComplete();
          }}
        >
          {formatMessage({ id: 'onboarding.launch' })}
        </Button>
      </Flex>

      <AppDrawer
        open={isWidgetOpen}
        onClose={() => setIsWidgetOpen(false)}
        size={400}
        overflowY="hidden"
        padding='0'
        title={
          <StyledText>{formatMessage({ id: 'common.talkToAgent' })}</StyledText>
        }
      >
        {isWidgetOpen ? <VoiceAgent agentData={agent} /> : null}
      </AppDrawer>
    </Fragment>
  );
};

export default FinalSummary;
