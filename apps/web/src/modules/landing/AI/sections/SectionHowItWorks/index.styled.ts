import styled from 'styled-components';
import { Typography } from 'antd';
import { OnestFontFamily } from '../../index.styled';

const Container = styled.div`
  width: 100%;
  max-width: 1200px;
  padding: 20px 0;
  margin: 0 auto;
`;

const Title = styled.h2`
  font-family: 'Oxanium', sans-serif;
  color: ${({ theme }) => theme.palette.text.heading};
  font-size: 3rem;
  text-align: center;
  font-weight: 600;
  margin-bottom: 3rem;
  span {
    color: ${({ theme }) => theme.palette.primary};
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    font-size: 42px !important;
    margin-bottom: 2rem;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    font-size: 38px !important;
    margin-bottom: 1.5rem;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 34px !important;
    margin-bottom: 1.25rem;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 28px !important;
    margin-bottom: 1rem;
  }
`;

const ContentColumn = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
`;

const ImageColumn = styled.div`
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const SectionWrapper = styled.div<{ $reverse?: boolean }>`
  display: flex;
  position: relative;
  flex-direction: ${(props) => (props.$reverse ? 'row-reverse' : 'row')};

  &:before {
    content: '';
    width: 28px;
    height: 28px;
    background-image: url('/images/landing/how-it-works/howitworks-dots.svg');
    background-size: contain;
    background-repeat: no-repeat;
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: 4px;
    z-index: 2;
    @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
      display: none;
    }
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    flex-direction: column;
    align-items: center;
    ${ImageColumn} {
      order: 1;
    }
    ${ContentColumn} {
      order: 2;
    }
  }
`;

const VerticalLine = styled.div`
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  background-image: linear-gradient(to bottom, #d1ccff1a, #3d2ad3, #d1ccff1a);
  top: 24px;
  bottom: 0;
  z-index: 1;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    display: none;
  }
`;

const ContentBox = styled.div<{ $reverse?: boolean }>`
  border-radius: 10px;
  margin: ${(props) => (props.$reverse ? '0 auto 0 40px' : '0 40px 0 auto')};

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    margin: 20px auto;
    padding: 10px 40px;
    text-align: center;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    margin: 20px auto;
    padding: 10px;
    text-align: center;
  }
`;

const SectionTitle = styled(Typography.Title)`
  color: ${({ theme }) => theme.palette.text.heading} !important;
  ${OnestFontFamily}
  @media (max-width: 768px) {
    font-size: 1.375rem !important;
  }
`;

const SectionDescription = styled(Typography.Paragraph)`
  color: ${({ theme }) => theme.palette.text.subheading};
  font-size: 1.125rem;
  ${OnestFontFamily}
  font-weight: 400;

  @media (max-width: 768px) {
    font-size: 1rem;
  }
`;

export {
  Container,
  Title,
  SectionWrapper,
  ContentColumn,
  ImageColumn,
  VerticalLine,
  ContentBox,
  SectionTitle,
  SectionDescription,
};
