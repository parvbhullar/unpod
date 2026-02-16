'use client';
import React from 'react';
import { Button } from 'antd';
import { MdArrowOutward } from 'react-icons/md';
import AppPageSection from '@unpod/components/common/AppPageSection';
import {
  StyledContainer,
  StyledContent,
  StyledSubTitle,
  StyledTitle,
} from './index.styled';
import { useRouter } from 'next/navigation';
import { useIntl } from 'react-intl';

const style = {
  background: 'url(/images/landing/how-it-works/howitworks-background.webp)',
  backgroundSize: 'cover',
  backgroundRepeat: 'repeat',
  backgroundPosition: 'center',
};

const SectionContactUs = () => {
  const router = useRouter();
  const { formatMessage } = useIntl();

  const handleContactUsClick = () => {
    router.push('/auth/signup/');
  };

  return (
    <AppPageSection style={style}>
      <StyledContainer>
        <StyledContent>
          <StyledTitle level={2}>
            {formatMessage({ id: 'landing.contactUsTitle' })}{' '}
            <span className="text-active">
              {formatMessage({ id: 'landing.contactUsHighlight' })}
            </span>
          </StyledTitle>

          <StyledSubTitle level={3}>
            {formatMessage({ id: 'landing.contactUsSubtitle' })}
          </StyledSubTitle>

          <Button
            type="primary"
            shape="round"
            iconPlacement="end"
            size="large"
            icon={<MdArrowOutward fontSize={24} />}
            onClick={handleContactUsClick}
          >
            {formatMessage({ id: 'common.contact' })}
          </Button>
        </StyledContent>
      </StyledContainer>
    </AppPageSection>
  );
};

export default SectionContactUs;
