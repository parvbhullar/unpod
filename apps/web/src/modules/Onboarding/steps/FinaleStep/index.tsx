'use client';
import React, { Fragment, useState } from 'react';
import { Button, Divider, Flex } from 'antd';
import { useIntl } from 'react-intl';
import { useRouter, useSearchParams } from 'next/navigation';
import IdentityCard from './IdentityCard';
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
import { DrawerBody } from '@unpod/components/antd';
import type { Organization, Pilot, User } from '@unpod/constants/types';

const VoiceAgent = dynamic<any>(
  () => import('@unpod/modules/AppAgentModule/VoiceAgent'),
  { ssr: false },
);

type FinalSummaryProps = {
  agent?: Pilot | null;
};

const FinalSummary: React.FC<FinalSummaryProps> = ({ agent }) => {
  const { formatMessage } = useIntl();
  const [loading, setLoading] = useState(false);
  const infoViewActionsContext = useInfoViewActionsContext();
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const onboarded = searchParams?.get('onboarded') === 'true';
  const { getSubscription, setActiveOrg, updateAuthUser } =
    useAuthActionsContext();
  const { startTour } = useTourActionsContext();
  const { activeOrg } = useAuthContext();

  const onComplete = () => {
    setLoading(true);
    getDataApi('auth/me/', infoViewActionsContext)
      .then((response) => {
        const res = response as {
          data?: User & {
            active_organization?: Organization;
            active_space?: { slug?: string };
          };
        };
        const data = res.data;
        if (!data) {
          throw new Error('No user data');
        }
        if (!data.active_organization) {
          throw new Error('No active organization');
        }
        setOrgHeader(data.active_organization.domain_handle);
        getSubscription();
        updateAuthUser(data);
        setActiveOrg({ ...activeOrg, ...data.active_organization });
        if (onboarded) {
          router.push(`/ai-studio/${agent?.handle}/`);
        } else {
          console.log('FinalSummary onComplete startTour', startTour);
          setActiveOrg({ ...activeOrg, ...data.active_organization });
          startTour();
          router.push(`/spaces/${data.active_space?.slug}/call/`);
        }
      })
      .catch((response) => {
        const err = response as { message?: string };
        infoViewActionsContext.showError(err.message || 'Error');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <Fragment>
      <IdentityCard agent={agent} />

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
          {formatMessage({ id: 'identityOnboarding.launch' })}
        </Button>
      </Flex>

      <AppDrawer
        padding="0"
        open={isWidgetOpen}
        onClose={() => setIsWidgetOpen(false)}
        size={400}
        title={
          <StyledText>{formatMessage({ id: 'common.talkToAgent' })}</StyledText>
        }
      >
        <DrawerBody overFlowY="hidden" bodyHeight={70}>
          {isWidgetOpen ? <VoiceAgent agentData={agent} /> : null}
        </DrawerBody>
      </AppDrawer>
    </Fragment>
  );
};

export default FinalSummary;
