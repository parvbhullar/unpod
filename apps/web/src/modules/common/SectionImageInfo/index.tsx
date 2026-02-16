import React from 'react';
import { Typography } from 'antd';
import AppPageSection from '@unpod/components/common/AppPageSection';
import AppImage from '@unpod/components/next/AppImage';
import {
  StyledContainer,
  StyledDescription,
  StyledImageWrapper,
  StyledTextContainer,
} from './index.styled';
import clsx from 'clsx';
import type { SectionImageInfoData } from '@unpod/constants/types';

const { Paragraph, Title } = Typography;

type SectionImageInfoProps = {
  data: SectionImageInfoData;
  textPosition?: 'left' | 'right';
};

const SectionImageInfo: React.FC<SectionImageInfoProps> = ({
  data,
  textPosition = 'left',
}) => {
  return (
    <AppPageSection bgColor={textPosition === 'right' ? '#fff' : 'transparent'}>
      <StyledContainer
        className={clsx({ 'reverse-position': textPosition === 'right' })}
      >
        <StyledTextContainer>
          <Title level={2}>{data.heading}</Title>
          {data.subHeading && <Title level={4}>{data.subHeading}</Title>}
          {data.description && <Paragraph>{data.description}</Paragraph>}

          <StyledDescription>
            {data.items?.map((item, index) => (
              <li key={index}>
                <span
                  className="item-name"
                  dangerouslySetInnerHTML={{ __html: item.description }}
                />
              </li>
            ))}
          </StyledDescription>
        </StyledTextContainer>
        <StyledImageWrapper>
          <AppImage
            src={data.image.url}
            alt={data.image.alt || 'Image'}
            layout="fill"
          />
        </StyledImageWrapper>
      </StyledContainer>
    </AppPageSection>
  );
};

export default SectionImageInfo;
