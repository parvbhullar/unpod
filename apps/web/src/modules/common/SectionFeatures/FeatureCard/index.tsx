'use client';
import React from 'react';
import { MdApps, MdLightbulbOutline, MdSearch } from 'react-icons/md';
import { GrConnect } from 'react-icons/gr';
import { BiImport } from 'react-icons/bi';
import {
  RiBracesLine,
  RiDatabase2Fill,
  RiErrorWarningLine,
  RiFileTextLine,
} from 'react-icons/ri';
import { GoWorkflow } from 'react-icons/go';
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
  instantly: <RiBracesLine fontSize={42} />,
  support: <MdApps fontSize={42} />,
  'red-flags': <RiErrorWarningLine fontSize={42} />,
  'document-search': <MdSearch fontSize={42} />,
  workflow: <GoWorkflow fontSize={42} />,
  'risk-assessment': <RiFileTextLine fontSize={42} />,
  connect: <GrConnect fontSize={42} />,
  import: <BiImport fontSize={42} />,
  database: <RiDatabase2Fill fontSize={42} />,
  decision: <MdLightbulbOutline fontSize={42} />,
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
