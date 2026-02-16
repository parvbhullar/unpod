'use client';

import type { ComponentType } from 'react';
import React, { useEffect, useState } from 'react';
import clsx from 'clsx';
import {
  getDataApi,
  uploadPostDataApi,
  uploadPutDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import Header from '../Onboarding/Header';
import StepHeader from '../Onboarding/StepHeader';
import IdentityStep from './IdentityStep';
import VoiceForm from './VoiceForm';
import FinalSummary from './FinaleStep';
import {
  StyledCollapse,
  StyledContainer,
  StyledContent,
  StyledPanel,
  StyledRoot,
} from './index.styled';
import { useSearchParams } from 'next/navigation';
import type { Pilot } from '@unpod/constants/types';

const IdentitySteps: Array<{
  step: number;
  title: string;
  description: string;
  component: ComponentType<any>;
}> = [
  {
    step: 1,
    title: 'identityOnboarding.identity',
    description: 'identityOnboarding.nameAndFunctions',
    component: IdentityStep,
  },
  {
    step: 2,
    title: 'identityOnboarding.voiceProfile',
    description: 'identityOnboarding.choosePerfectVoice',
    component: VoiceForm,
  },
  {
    step: 3,
    title: 'identityOnboarding.launch',
    description: 'identityOnboarding.identityReady',
    component: FinalSummary,
  },
];

const BusinessIdentity = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const searchParams = useSearchParams();
  const agentHandle = searchParams?.get('handle');

  const [activeStep, setActiveStep] = useState(1);
  const [unlockedStep, setUnlockedStep] = useState(1);
  const [agent, setAgent] = useState<Pilot | null>(null);

  useEffect(() => {
    if (agentHandle && !agent) {
      getDataApi<Pilot>(`/core/pilots/${agentHandle}/`, infoViewActionsContext)
        .then((data) => {
          setAgent(data.data || null);
        })
        .catch((error) => {
          const payload = error as { message?: string };
          infoViewActionsContext.showError(payload.message || '');
        });
    }
  }, [agent]);

  const goToNextStep = () => {
    const nextStepKey = activeStep + 1;
    setActiveStep(nextStepKey);
    if (nextStepKey > unlockedStep) setUnlockedStep(nextStepKey);
  };

  const updateAgentData = (
    formData: FormData | null,
    setLoading?: (loading: boolean) => void,
  ) => {
    if (formData) {
      setLoading?.(true);
      const apiMethod = agent?.handle ? uploadPutDataApi : uploadPostDataApi;
      const url = agent?.handle
        ? `/core/pilots/${agent.handle}/`
        : `core/pilots/`;

      apiMethod<Pilot>(url, infoViewActionsContext, formData)
        .then((data) => {
          infoViewActionsContext.showMessage(data.message || '');
          setAgent((prev) => ({
            ...(prev || {}),
            ...(data.data || {}),
          }));

          goToNextStep();
        })
        .catch((error) => {
          const payload = error as { message?: string };
          infoViewActionsContext.showError(payload.message || '');
        })
        .finally(() => {
          setLoading?.(false);
        });
    } else {
      setActiveStep(activeStep + 1);
    }
  };

  const onKeyChange = (key: string) => {
    if (key) {
      const stepKey = parseInt(key);

      if (stepKey <= unlockedStep) {
        setActiveStep(stepKey);
      }
    }
  };

  return (
    <StyledRoot>
      <Header />
      <StyledContainer>
        <StyledContent>
          <StyledCollapse
            accordion
            expandIconPlacement="end"
            activeKey={activeStep}
            onChange={(keys) => {
              onKeyChange(keys?.[0]);
            }}
          >
            {IdentitySteps.map(
              ({ step, component: Component, ...restInfo }) => (
                <StyledPanel
                  key={step}
                  className={clsx({ success: step < activeStep })}
                  header={
                    <StepHeader
                      step={step}
                      activeStep={activeStep}
                      {...restInfo}
                    />
                  }
                >
                  <Component
                    agent={agent}
                    setAgent={setAgent}
                    updateAgentData={updateAgentData}
                  />
                </StyledPanel>
              ),
            )}
          </StyledCollapse>
        </StyledContent>
      </StyledContainer>
    </StyledRoot>
  );
};

export default BusinessIdentity;
