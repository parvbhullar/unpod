'use client';

import React, { Fragment, useCallback, useEffect, useRef } from 'react';
import AppImage from '@unpod/components/next/AppImage';
import {
  getDataApi,
  postDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { PUBLIC_EMAIL_DOMAIN } from '@unpod/constants';
import { useRouter } from 'next/navigation';
import { generateHandle, getRandomColor } from '@unpod/helpers';
import { setOrgHeader } from '@unpod/services';
import {
  LogoInner,
  LogoWrapper,
  OuterGlow,
  ProgressBarContainer,
  ProgressBarFill,
  ProgressInfo,
  ProgressPercent,
  ProgressStep,
  ProgressWrapper,
  SpinnerRing,
  StatusDot,
  StatusText,
  StatusWrapper,
  StyledContainer,
  StyledSubtitle,
  StyledTitle,
} from './index.styled';
import { type IntlShape, useIntl } from 'react-intl';
import type { Organization, Pilot } from '@unpod/constants/types';

const getProgressStep = (
  progress: number,
  formatMessage: IntlShape['formatMessage'],
) => {
  if (progress < 30)
    return formatMessage({ id: 'onboarding.fetchingBusinessInfo' });
  if (progress < 70)
    return formatMessage({ id: 'onboarding.creatingBusinessIdentity' });
  if (progress < 100)
    return formatMessage({ id: 'onboarding.settingUpAiAgent' });
  return formatMessage({ id: 'onboarding.completingSetup' });
};

const CreatingIdentity = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { updateAuthUser, setActiveOrg } = useAuthActionsContext();
  const { user } = useAuthContext();
  const router = useRouter();
  const { formatMessage } = useIntl();

  const [progress, setProgress] = React.useState(0);
  const targetProgressRef = useRef(45);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Gradually increment progress until it reaches target
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setProgress((prev) => {
        const target = targetProgressRef.current;
        if (prev < target) {
          // Increment by 1, but slow down as we approach target
          const remaining = target - prev;
          const increment = remaining > 10 ? 2 : 1;
          return Math.min(prev + increment, target);
        }
        return prev;
      });
    }, 200);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const setTargetProgress = useCallback((target: number) => {
    targetProgressRef.current = target;
    setProgress(target); // Jump to milestone immediately when API completes
  }, []);

  type BusinessData = {
    company_name?: string;
    description?: string;
    ai_agent: {
      name?: string;
      description?: string;
      system_prompt?: string;
      persona?: string;
    };
    visual: {
      brand_colors?: string[];
      logo_url?: string;
    };
  };

  const createBusinessAiAgent = (domain: string, data: BusinessData) => {
    targetProgressRef.current = 95; // Allow gradual increment up to 95%

    const payload = {
      name: data.ai_agent.name || data.company_name,
      handle: generateHandle(data.ai_agent.name || data.company_name, 8),
      description: data.ai_agent.description,
      privacy_type: 'public',
      type: 'Voice',
      purpose: 'Business',
      conversation_tone: 'Professional',
      system_prompt: data.ai_agent.system_prompt || '',
      ai_persona: data.ai_agent.persona || '',
    };

    postDataApi<Pilot>('core/pilots/', infoViewActionsContext, payload)
      .then((response) => {
        setTargetProgress(100);
        router.push(`/business-identity/?handle=${response.data?.handle}`);
      })
      .catch((error: { message?: string }) => {
        console.error('Error creating business agent:', error.message);
        infoViewActionsContext.showError(
          error.message || 'Failed to create agent',
        );
      });
  };

  const createBusinessIdentity = (domain: string, data: BusinessData) => {
    targetProgressRef.current = 65; // Allow gradual increment up to 65%

    const colors = data.visual.brand_colors || [];
    const primaryColor = colors[0] || getRandomColor();

    const payload = {
      domain_handle: domain,
      name: data.company_name,
      description: data.description,
      privacy_type: 'public',
      account_type: 'business',
      region: 'IN',
      color: primaryColor,
      logo_external_url: data.visual.logo_url || '',
    };

    postDataApi<Organization>(
      'organization/',
      infoViewActionsContext,
      payload,
    )
      .then((response) => {
        setTargetProgress(70);
        setOrgHeader(response.data?.domain_handle || '');
        updateAuthUser({
          ...user,
          organization: response.data,
          active_organization: response.data,
          organization_list: [
            ...(user?.organization_list || []),
            ...(response.data ? [response.data] : []),
          ],
        });
        if (response.data) {
          setActiveOrg(response.data);
        }
        createBusinessAiAgent(domain, data);
      })
      .catch((error: { message?: string }) => {
        console.error('Error creating business identity:', error.message);
        infoViewActionsContext.showError(
          error.message || 'Failed to create identity',
        );
      });
  };

  const fetchBusinessIdentity = (domain: string) => {
    getDataApi<BusinessData>(`core/website-info/`, infoViewActionsContext, {
      domain,
    })
      .then((response) => {
        setTargetProgress(30);
        if (response.data) {
          createBusinessIdentity(domain, response.data);
        }
      })
      .catch((error: { message?: string }) => {
        console.error('Error fetching business identity:', error.message);
        infoViewActionsContext.showError(
          error.message || 'Failed to fetch identity',
        );
      });
  };

  useEffect(() => {
    const emailDomain = user?.email?.split('@')[1] || '';
    const isPublic = PUBLIC_EMAIL_DOMAIN.includes(
      emailDomain as (typeof PUBLIC_EMAIL_DOMAIN)[number],
    );
    if (user?.is_private_domain || !isPublic) {
      fetchBusinessIdentity(user?.domain || emailDomain);
    } else {
      router.push('/business-identity/');
    }
  }, []);

  return (
    <StyledContainer>
      <LogoWrapper>
        <OuterGlow />
        <SpinnerRing />
        <LogoInner>
          <AppImage
            src="/images/unpod/logo-icon.svg"
            alt="Unpod"
            width={100}
            height={100}
          />
        </LogoInner>
      </LogoWrapper>

      {user?.is_private_domain && (
        <Fragment>
          <StyledTitle level={2}>
            {formatMessage({ id: 'onboarding.creatingBusinessTitle' })}
          </StyledTitle>
          <StyledSubtitle>
            {formatMessage({ id: 'onboarding.creatingBusinessSubtitle' })}
          </StyledSubtitle>

          <StatusWrapper>
            <StatusDot />
            <StatusText>
              {formatMessage({ id: 'onboarding.settingUpSecurely' })}
            </StatusText>
          </StatusWrapper>

          <ProgressWrapper>
            <ProgressBarContainer>
              <ProgressBarFill $progress={progress} />
            </ProgressBarContainer>
            <ProgressInfo>
              <ProgressStep>
                {getProgressStep(progress, formatMessage)}
              </ProgressStep>
              <ProgressPercent>{progress}%</ProgressPercent>
            </ProgressInfo>
          </ProgressWrapper>

          {/*<SecureText>
            <SafetyOutlined />
            Your data is encrypted and secure
          </SecureText>*/}
        </Fragment>
      )}
    </StyledContainer>
  );
};

export default CreatingIdentity;
