import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import AppImage from '@unpod/components/next/AppImage';
import {
  StyledContainer,
  StyledImageWrapper,
  StyledSubTitle,
  StyledTextContainer,
  StyledTitle,
} from './index.styled';

const SectionSolvesProblems = () => {
  return (
    <AppPageSection bgColor="#fff">
      <StyledContainer>
        <StyledTextContainer>
          <StyledTitle level={2}>
            Create an AI That{' '}
            <span className="text-active">Solves Problems</span> with Your
            Expertise
          </StyledTitle>
          <StyledSubTitle level={4}>
            Create an AI That Solves Problems with Your ExpertiseCreate an AI
            that performs a specific task or provides answers in a particular
            area, using only your knowledge and experience.
          </StyledSubTitle>
        </StyledTextContainer>
        <StyledImageWrapper>
          <AppImage
            src="/images/landing/ai-solve-problems.svg"
            alt="Apps"
            layout="fill"
          />
        </StyledImageWrapper>
      </StyledContainer>
    </AppPageSection>
  );
};

export default SectionSolvesProblems;
