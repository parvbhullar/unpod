'use client';
import React, { useState } from 'react';
import { Collapse, Flex } from 'antd';
import {
  uploadPostDataApi,
  uploadPutDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import {
  CollapseWrapper,
  Container,
  MainContent,
  StyledMainContainer,
  StyledPanel,
  StyledRoot,
} from './index.styled';
import VoiceForm from './steps/VoiceForm';
import Telephony from './steps/Telephony';
import FinalSummary from './steps/FinaleStep';
import Header from './Header';
import IdentityStep from './steps/IdentityStep';
import PersonaStep from './steps/PersonaStep';
import CustomStepper from '@/modules/Onboarding/steps';
import type { Pilot } from '@unpod/constants/types';

const OnBoarding = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [activeKey, setActiveKey] = useState('1');
  const [agent, setAgent] = useState<Pilot>({
    name: '',
    handle: '',
  });
  const [highestUnlockedStep, setHighestUnlockedStep] = useState(1);
  const [domainData, setDomainData] = useState<{
    ai_agent?: { system_prompt?: string };
  } | null>(null);

  const goToNextStep = (nextStepKey: string) => {
    const next = parseInt(nextStepKey, 10);
    setActiveKey(nextStepKey);
    if (next > highestUnlockedStep) setHighestUnlockedStep(next);
  };

  const updateAgentData = (
    formData: FormData,
    setLoading?: React.Dispatch<React.SetStateAction<boolean>>,
    nextStepKey?: string,
  ) => {
    if (formData) {
      setLoading?.(true);
      const apiMethod = agent?.handle ? uploadPutDataApi : uploadPostDataApi;
      const url = agent?.handle
        ? `/core/pilots/${agent.handle}/`
        : `core/pilots/`;

      apiMethod<Partial<Pilot>>(url, infoViewActionsContext, formData)
        .then((data) => {
          infoViewActionsContext.showMessage(data.message || 'Saved');
          setAgent((prev) => ({
            ...prev,
            ...(data.data || {}),
          }));

          if (nextStepKey) setActiveKey(nextStepKey);
          if (nextStepKey) goToNextStep(nextStepKey);
        })
        .catch((error) => {
          const err = error as { message?: string };
          infoViewActionsContext.showError(err.message || 'Error');
        })
        .finally(() => {
          setLoading?.(false);
        });
    } else {
      if (nextStepKey) setActiveKey(nextStepKey);
    }
  };

  const getClass = (currentStep: number) => {
    return currentStep < parseInt(activeKey, 10) ? 'success' : '';
  };

  const onKeyChange = (key: string | string[]) => {
    const nextKey = parseInt(Array.isArray(key) ? key[0] : key, 10);
    if (nextKey <= highestUnlockedStep) {
      setActiveKey(Array.isArray(key) ? key[0] : key);
    }
  };

  return (
    <Flex vertical>
      <Container>
        <MainContent>
          <Header />
          <StyledRoot>
            <StyledMainContainer>
              <CollapseWrapper>
                <Collapse
                  accordion
                  expandIconPlacement="end"
                  activeKey={activeKey}
                  onChange={(key) => {
                    onKeyChange(key);
                  }}
                >
                  <StyledPanel
                    key={'1'}
                    className={getClass(1)}
                    header={<CustomStepper step={1} activeKey={activeKey} />}
                  >
                    <IdentityStep
                      agent={agent}
                      updateAgentData={updateAgentData}
                      setAgent={setAgent}
                      setDomainData={setDomainData}
                    />
                  </StyledPanel>

                  <StyledPanel
                    key={'2'}
                    className={getClass(2)}
                    header={<CustomStepper step={2} activeKey={activeKey} />}
                  >
                    <PersonaStep
                      agent={agent}
                      updateAgentData={updateAgentData}
                      setAgent={setAgent}
                      domainData={domainData || undefined}
                    />
                  </StyledPanel>

                  <StyledPanel
                    key={'3'}
                    className={getClass(3)}
                    header={<CustomStepper step={3} activeKey={activeKey} />}
                  >
                    <VoiceForm
                      agent={agent}
                      setAgent={setAgent}
                      updateAgentData={updateAgentData}
                    />
                  </StyledPanel>

                  <StyledPanel
                    key={'4'}
                    className={getClass(4)}
                    header={<CustomStepper step={4} activeKey={activeKey} />}
                  >
                    <Telephony
                      agent={agent}
                      updateAgentData={updateAgentData}
                    />
                  </StyledPanel>

                  <StyledPanel
                    className={getClass(5)}
                    key={'5'}
                    header={<CustomStepper step={5} activeKey={activeKey} />}
                  >
                    <FinalSummary agent={agent} />
                  </StyledPanel>
                </Collapse>
              </CollapseWrapper>
            </StyledMainContainer>
          </StyledRoot>
        </MainContent>
      </Container>
    </Flex>
  );
};

export default OnBoarding;
