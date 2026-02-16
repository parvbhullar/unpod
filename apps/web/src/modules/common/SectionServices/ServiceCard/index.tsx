import React from 'react';
import { MdApps, MdSearch } from 'react-icons/md';
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
  assignment: <MdSearch fontSize={80} />,
  security: <MdApps fontSize={80} />,
  strategic: <RiFileTextLine fontSize={80} />,
};

type ServiceCardProps = {
  data: SectionListItem;
};

const ServiceCard: React.FC<ServiceCardProps> = ({ data }) => {
  const iconKey = data.icon as keyof typeof ICONS | undefined;
  return (
    <StyledRoot>
      <StyledIconBox>
        <StyledIconWrapper>
          {(iconKey && ICONS[iconKey]) || <MdApps fontSize={80} />}
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

export default ServiceCard;
