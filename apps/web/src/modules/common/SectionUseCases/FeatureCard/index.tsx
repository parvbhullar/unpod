import React from 'react';
import { MdApps, MdOutlineRealEstateAgent } from 'react-icons/md';
import { GiPayMoney, GiReceiveMoney } from 'react-icons/gi';
import { GrMoney } from 'react-icons/gr';
import { RiFileTextLine } from 'react-icons/ri';
import {
  StyledContent,
  StyledIconBox,
  StyledIconWrapper,
  StyledParagraph,
  StyledRoot,
  StyledTitle,
} from './index.styled';
import type { SectionListItem } from '@unpod/constants/types';

const ICONS = {
  'real-estate': <MdOutlineRealEstateAgent fontSize={42} />,
  'tax-credit': <GiPayMoney fontSize={42} />,
  'private-equity': <GiReceiveMoney fontSize={42} />,
  'venture-capital': <GrMoney fontSize={42} />,
  'notices-orders': <RiFileTextLine fontSize={42} />,
};

type FeatureCardProps = {
  data: SectionListItem;
};

const FeatureCard: React.FC<FeatureCardProps> = ({ data }) => {
  const iconKey = data.icon as keyof typeof ICONS | undefined;
  return (
    <StyledRoot>
      <StyledIconBox>
        <StyledIconWrapper>
          {(iconKey && ICONS[iconKey]) || <MdApps fontSize={42} />}
        </StyledIconWrapper>
      </StyledIconBox>

      <StyledContent>
        <StyledTitle>{data.title}</StyledTitle>
        <StyledParagraph className="item-description">
          {data.description}
        </StyledParagraph>
      </StyledContent>
    </StyledRoot>
  );
};

export default FeatureCard;
