import React from 'react';
// import { TextLoop } from 'react-text-loop-next';
import styled, { keyframes } from 'styled-components';

const keywords = [
  'individuals',
  'teachers',
  'authors',
  'scientists',
  'researchers',
  'engineers',
  'programmers',
  'organisations',
  'ai characters',
];

const AnimationText = () => {
  return (
    <>
      {/* <TextLoop springConfig={{ stiffness: 170, damping: 60 }} adjustingSpeed={0}>*/}
      {keywords.map((keyword, index) => (
        <StyledWrapper key={index}>{keyword}!</StyledWrapper>
      ))}
      {/* </TextLoop>*/}
    </>
  );
};

export default React.memo(AnimationText);

const animation = keyframes`
  0% {
    opacity: 0;
    transform: translateX(-50px) skewY(0deg) skewX(0deg) rotateZ(0deg);
    filter: blur(10px);
  }
  25% {
    opacity: 1;
    transform: translateY(0px) skewY(0deg) skewX(0deg) rotateZ(0deg);
    filter: blur(0px);
  }
  75% {
    opacity: 1;
    transform: translateY(0px) skewY(0deg) skewX(0deg) rotateZ(0deg);
    filter: blur(0px);
  }
  100% {
    opacity: 0;
    transform: translateY(30px) skewY(0deg) skewX(0deg) rotateZ(0deg);
    filter: blur(10px);
  }
`;

const StyledWrapper = styled.span`
  display: inline-block;
  color: ${({ theme }) => theme.palette.primary};
  font-weight: bold;
  /*opacity: 0;
  animation-name: ${animation};
  animation-duration: 5s;
  animation-fill-mode: forwards;
  animation-iteration-count: infinite;
  animation-timing-function: cubic-bezier(0.075, 0.82, 0.165, 1);*/
`;
