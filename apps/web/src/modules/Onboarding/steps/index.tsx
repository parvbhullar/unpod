'use client';
import React from 'react';
import { useIntl } from 'react-intl';
import { CustomSteps, StyledStepsIcon } from './index.styled';

type CustomStepperProps = {
  step: number;
  activeKey: string;
};

const CustomStepper: React.FC<CustomStepperProps> = ({ step, activeKey }) => {
  const { formatMessage } = useIntl();
  const success = step < parseInt(activeKey);
  const active = parseInt(activeKey) === step;

  const stepsList = [
    {
      title: formatMessage({ id: 'identityOnboarding.identity' }),
      description: formatMessage({ id: 'identityOnboarding.nameAndFunctions' }),
    },
    {
      title: formatMessage({ id: 'identityOnboarding.persona' }),
      description: formatMessage({ id: 'identityOnboarding.aiPoweredScript' }),
    },
    {
      title: formatMessage({ id: 'identityOnboarding.voiceProfile' }),
      description: formatMessage({
        id: 'identityOnboarding.choosePerfectVoice',
      }),
    },
    {
      title: formatMessage({ id: 'identityOnboarding.telephony' }),
      description: formatMessage({
        id: 'identityOnboarding.choosePerfectPhone',
      }),
    },
    {
      title: formatMessage({ id: 'identityOnboarding.launch' }),
      description: formatMessage({ id: 'identityOnboarding.identityReady' }),
    },
  ];

  const singleStep = [
    {
      ...stepsList[step - 1],
      icon: (
        <StyledStepsIcon
          className={success ? 'success' : active ? 'active' : ''}
        >
          {step}
        </StyledStepsIcon>
      ),
    },
  ];
  return <CustomSteps direction="horizontal" current={0} items={singleStep} />;
};

export default CustomStepper;
