import styled from 'styled-components';
import { GlobalTheme } from '@unpod/constants';

export const StyledBannerContainer = styled.div`
  width: ${({ theme }: { theme: GlobalTheme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 16px auto 0 auto;
  text-align: center;

  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.md + 75}px) {
    margin: 0 auto 16px;
  }
`;

export const StyledImageWrapper = styled.div`
  position: relative;
  border-radius: ${({ theme }: { theme: GlobalTheme }) =>
    theme.component.card.borderRadius};
  overflow: hidden;
  margin-bottom: 16px;

  & .banner-img {
    width: 100%;
    height: 100%;
    max-height: 330px;
    object-fit: cover;
  }
`;

export const StyledTextWrapper = styled.div`
  margin-bottom: 16px;
  margin-inline: auto;
  max-width: 530px;
`;
