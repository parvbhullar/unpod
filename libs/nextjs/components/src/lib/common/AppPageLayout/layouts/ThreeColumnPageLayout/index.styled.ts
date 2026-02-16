import styled from 'styled-components';

export type LayoutType = 'full' | 'two-columns' | 'three-columns';

const setLayoutType = (layoutType: LayoutType) => {
  switch (layoutType) {
    case 'full':
      return `
            grid-template-columns: 1fr;
            grid-template-areas: 'content';
        `;
    case 'two-columns':
      return `
            grid-template-columns: auto 1fr;
            grid-template-areas: 'sidebar content';
        `;
    case 'three-columns':
      return `
            grid-template-columns: 1fr auto 1fr;
            grid-template-areas: 'sidebar content rightSidebar';
        `;
    default:
      return `
            grid-template-columns: 1fr auto 1fr;
            grid-template-areas: 'sidebar content rightSidebar';
        `;
  }
};

export const StyledMainContainer = styled.div`
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  padding: 0;
`;

export const StyledPageRoot = styled.div<{ $layoutType: LayoutType }>`
  flex: 1;
  margin: 0;
  display: grid;
  ${({ $layoutType }) => setLayoutType($layoutType)};
  // overflow: auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.xl - 1}px) {
    display: block;
  }
`;
