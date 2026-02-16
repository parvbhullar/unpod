import styled from 'styled-components';
import { Typography } from 'antd';
import { OnestFontFamily } from '../../index.styled';

const { Title, Paragraph } = Typography;

export const StyledRoot = styled.section`
  min-height: 95vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem 8rem;
  text-align: center;
  background:
    radial-gradient(
      circle at 35% 40%,
      rgba(55, 125, 255, 0.25) 0%,
      transparent 25%
    ),
    radial-gradient(
      circle at 65% 60%,
      rgba(168, 57, 255, 0.25) 0%,
      transparent 25%
    ),
    linear-gradient(180deg, #f2eeff 0%, #ffeffd 50%, #f2eeff 100%);
  position: relative;
  overflow: hidden;
`;

export const StyledTaglineWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 50px;
`;

export const StyledTagline = styled.div`
  ${OnestFontFamily}
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 5px;
  padding: 11px 46px 7px;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: 24px;
  margin-block: 16px;
  color: ${({ theme }) => theme.palette.text.heading};
  font-weight: 500;

  & .text {
    margin-bottom: 2px;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 14px;
    text-align: center;
    border-radius: 16px;
  }
`;

export const StyledSubTitle = styled(Title)`
  ${OnestFontFamily}
  font-size: 20px !important;
  font-weight: 400 !important;
  margin: 16px auto !important;
  color: ${({ theme }) => theme.palette.text.subheading} !important;
  max-width: 700px;
`;

export const StyledTitle = styled(Title)`
  font-family: 'Oxanium', sans-serif;
  font-size: 52px !important;
  font-weight: 600 !important;
  line-height: 1.1 !important;
  margin: 1.5rem 0 !important;
  color: ${({ theme }) => theme.palette.text.heading} !important;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    font-size: 40px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    font-size: 36px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 32px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 26px !important;
  }
`;

export const StyledWordPressTitle = styled.span`
  font-family: var(--font-eb-garamond), 'EB Garamond', serif;
  color: #3858e9;
  font-weight: 500;
  margin-bottom: 10px;
`;

export const StyledOrangeText = styled.span`
  color: #f86232;
`;

export const StyledPurpleText = styled.span`
  color: ${({ theme }) => theme.palette.primary};
`;

export const StyledContainer = styled.div`
  margin: 0 auto 8em;
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition: margin 0.8s;
`;

export const StyledActionsWrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 24px;
  flex-wrap: wrap;
  gap: 16px;
`;

export const StyledGitHubButton = styled.a`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background-color: #24292f;
  color: #ffffff;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;

  & .star-icon {
    color: #ffd700;
  }

  &:hover {
    background-color: #000000;
    color: #ffffff;
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 8px 16px;
    font-size: 13px;
  }
`;

export const CarouselContainer = styled.div`
  width: 100%;
  position: relative;
  padding: 12px 24px;

  .ant-carousel .slick-dots {
    bottom: -30px;
  }

  .ant-carousel .slick-dots li button {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.1);
  }

  .ant-carousel .slick-dots li.slick-active button {
    background: ${({ theme }) => theme.palette.primary};
  }

  .ant-carousel .slick-list {
    margin: 0 -10px;
    padding: 20px 0;
  }

  .ant-carousel .slick-slide {
    padding: 0 10px;
  }

  .ant-carousel .slick-slide > div {
    height: 100%;
  }
`;

export const CarouselWrapper = styled.div`
  display: flex;
  gap: 1.5rem;
`;

export const StyledCard = styled.div`
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
  height: 350px;
  max-width: 375px;
  position: relative;
  background-size: cover;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  }
`;

export const StyledCardContent = styled.div`
  position: absolute;
  bottom: 0;
  padding: 1.25rem 2.125rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 100%;
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 1rem;
  }
`;

export const StyledCardTitle = styled(Title)`
  font-size: 1.5rem !important;
  font-weight: 400 !important;
  margin-bottom: 0 !important;
  ${OnestFontFamily}
  color: ${({ theme }) => theme.palette.text.heading} !important;
`;

export const StyledCardSubtitle = styled(Paragraph)`
  font-size: 0.875rem;
  color: ${({ theme }) => theme.palette.text.subheading};
  margin-bottom: 0 !important;
  ${OnestFontFamily}
  font-weight: 500;
`;

export const StyledBadgesContainer = styled.div`
  display: flex;
  position: absolute;
  top: 12px;
  left: 12px;
  gap: 6px;
`;

export const StyledBadge = styled.div`
  font-size: 0.8rem;
  background-color: ${({ theme }) => theme.palette.background.default};
  color: ${({ theme }) => theme.palette.text.heading};
  padding: 3px 7px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  ${OnestFontFamily}
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(2px);
  margin: 0;
  letter-spacing: 0.2px;
`;

export const StyledCardDescription = styled(Paragraph)`
  font-size: 0.875rem;
  color: ${({ theme }) => theme.palette.text.subheading};
  line-height: 1.5;
  ${OnestFontFamily}
  opacity: 0.9;
`;

export const NavButton = styled.button`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: white;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  cursor: pointer;
  opacity: 0.9;
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;

  &:hover {
    opacity: 1;
    transform: translateY(-50%) scale(1.05);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
`;
