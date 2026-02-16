'use client';
import styled from 'styled-components';

export const StyledRoot = styled.div`
  text-align: center;
  max-width: 900px;
  margin: 0 auto;
`;

export const StyledHeroSection = styled.div`
  margin-bottom: 60px;

  .hero-title {
    font-family: 'Oxanium', sans-serif;
    font-size: 52px !important;
    font-weight: 600 !important;
    margin-bottom: 16px !important;
    color: ${({ theme }) => theme.palette.text.heading} !important;
    text-align: center;

    .text-active {
      background: linear-gradient(90deg, #377dff 0%, #a839ff 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

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
  }

  .hero-description {
    font-size: 18px;
    color: ${({ theme }) => theme.palette.text.secondary};
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.6;

    @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
      font-size: 16px;
    }
  }
`;

export const StyledDownloadCards = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 60px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    grid-template-columns: 1fr;
  }
`;

export const StyledDownloadCard = styled.div<{ $isCurrentOS?: boolean }>`
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.radius.base}px;
  box-shadow: ${({ $isCurrentOS }) =>
    $isCurrentOS
      ? '0 8px 32px rgba(121, 108, 255, 0.25)'
      : '0 2px 8px rgba(0, 0, 0, 0.06)'};
  border: 2px solid
    ${({ $isCurrentOS, theme }) =>
      $isCurrentOS ? theme.palette.primary : theme.border.color};
  padding: 32px 24px;
  padding-top: ${({ $isCurrentOS }) => ($isCurrentOS ? '16px' : '32px')};
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.3s ease;
  position: relative;
  transform: ${({ $isCurrentOS }) =>
    $isCurrentOS ? 'scale(1.02)' : 'scale(1)'};

  &:hover {
    transform: ${({ $isCurrentOS }) =>
      $isCurrentOS ? 'scale(1.02) translateY(-4px)' : 'translateY(-4px)'};
    box-shadow: ${({ $isCurrentOS }) =>
      $isCurrentOS
        ? '0 12px 40px rgba(121, 108, 255, 0.3)'
        : '0 8px 24px rgba(0, 0, 0, 0.08)'};
  }

  .recommended-tag {
    margin-bottom: 12px;
    font-size: 12px;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 12px;
  }

  .platform-icon {
    width: 64px;
    height: 64px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 48px;
    color: ${({ $isCurrentOS, theme }) =>
      $isCurrentOS ? theme.palette.primary : theme.palette.text.primary};
  }

  .platform-name {
    font-size: 24px;
    font-weight: ${({ theme }) => theme.font.weight.semiBold};
    color: ${({ theme }) => theme.palette.text.heading};
    margin-bottom: 8px;
  }

  .platform-version {
    font-size: 14px;
    color: ${({ theme }) => theme.palette.text.secondary};
    margin-bottom: 20px;
  }

  .download-btn {
    min-width: 200px;
    height: 48px;
    font-size: 15px;
    font-weight: ${({ theme }) => theme.font.weight.medium};
    border-radius: 24px;
    background: linear-gradient(90deg, #377dff 0%, #a839ff 100%);
    border: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;

    &:hover {
      background: linear-gradient(90deg, #2a6ce8 0%, #9530e8 100%);
    }

    .anticon {
      font-size: 16px;
    }
  }

  .architecture-links {
    margin-top: 12px;
    display: flex;
    gap: 16px;
    font-size: 13px;

    a {
      color: ${({ theme }) => theme.palette.text.secondary};
      text-decoration: none;
      transition: color 0.2s ease;

      &:hover {
        color: ${({ theme }) => theme.palette.primary};
      }
    }
  }
`;

export const StyledRequirementsSection = styled.div`
  margin-top: 20px;
`;

export const StyledRequirementsTitle = styled.h2`
  font-family: 'Oxanium', sans-serif;
  color: ${({ theme }) => theme.palette.text.heading};
  font-size: 2.5rem;
  text-align: center;
  font-weight: 600;
  margin-bottom: 2.5rem;

  span {
    background: linear-gradient(90deg, #377dff 0%, #a839ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 2rem;
    margin-bottom: 2rem;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 1.75rem;
    margin-bottom: 1.5rem;
  }
`;

export const StyledRequirementsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    grid-template-columns: 1fr;
  }
`;

export const StyledRequirementCard = styled.div`
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: 24px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  transition: all 0.3s ease;
  border: 1px solid transparent;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(121, 108, 255, 0.12);
    border-color: ${({ theme }) => theme.palette.primary}20;
  }

  .requirement-icon {
    width: 48px;
    height: 48px;
    min-width: 48px;
    border-radius: 12px;
    background: linear-gradient(135deg, #f4f0ff 0%, #ffeffd 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: ${({ theme }) => theme.palette.primary};
  }

  .requirement-content {
    flex: 1;

    h4 {
      font-size: 16px;
      font-weight: ${({ theme }) => theme.font.weight.semiBold};
      color: ${({ theme }) => theme.palette.text.heading};
      margin: 0 0 6px 0;
    }

    p {
      font-size: 14px;
      color: ${({ theme }) => theme.palette.text.secondary};
      margin: 0;
      line-height: 1.5;
    }
  }
`;
