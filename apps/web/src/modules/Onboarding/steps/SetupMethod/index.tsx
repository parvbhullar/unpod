import React from 'react';
import { StyledGrid } from './index.styled';
import AllIdentityCard from '../../AllIdentityCard';
import PlatformInput from '../../PlatformInput';
import { IoSettingsOutline } from 'react-icons/io5';
import { LuGlobe } from 'react-icons/lu';
import StepHeader from '../StepHeader';
import { StyledInnerContainer } from '@/modules/Onboarding/index.styled';
import { useIntl } from 'react-intl';

type CreationMethod = {
  id: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  IconBgColor: string;
  type: string;
  inputTitle?: string;
  placeholder?: string;
  url?: string;
};

type SetupMethodProps = {
  selectedCard?: string;
  setSelectedCard: (value: string) => void;
  setBasicDetail: (detail: string) => void;
  currentStep?: number;
};

export const SetupMethod: React.FC<SetupMethodProps> = ({
  selectedCard,
  setSelectedCard,
  setBasicDetail,
}) => {
  const { formatMessage } = useIntl();

  const creationMethods: CreationMethod[] = [
    {
      id: 1,
      title: formatMessage({ id: 'onboarding.createManually' }),
      description: formatMessage({ id: 'onboarding.createManuallyDesc' }),
      icon: <IoSettingsOutline size={24} />,
      IconBgColor: '#796CFF',
      type: 'manual',
      inputTitle: '',
      url: '',
    },
    {
      id: 5,
      title: formatMessage({ id: 'onboarding.websiteLink' }),
      description: formatMessage({ id: 'onboarding.websiteLinkDesc' }),
      icon: <LuGlobe size={24} />,
      IconBgColor: '#796CFF',
      type: 'website',
      placeholder: 'https://example.com',
      inputTitle: formatMessage({ id: 'onboarding.website' }),
    },
  ];

  return (
    <>
      <StyledInnerContainer>
        <StepHeader />
        <StyledGrid>
          <AllIdentityCard
            creationMethods={creationMethods}
            selectedCard={selectedCard}
            setSelectedCard={setSelectedCard}
          />
        </StyledGrid>
        {selectedCard &&
          selectedCard !== 'manual' &&
          creationMethods
            .filter((method) => method.type === selectedCard)
            .map((creationMethod) => (
              <PlatformInput
                key={creationMethod.id}
                title={creationMethod.inputTitle}
                placeholder={creationMethod.placeholder}
                setBasicDetail={setBasicDetail}
              />
            ))}
      </StyledInnerContainer>
    </>
  );
};

export default SetupMethod;
