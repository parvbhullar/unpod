import styled from 'styled-components';

export const StyledSection = styled.section`
  width: 100vw;
  background: #fff;
  padding: 64px 0 36px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

export const StyledHeadline = styled.h2`
  font-size: 2.2rem;
  font-weight: 800;
  color: #181c32;
  text-align: center;
  margin-bottom: 10px;
`;

export const StyledSubtitle = styled.p`
  color: #6b6f81;
  font-size: 1.11rem;
  text-align: center;
  margin: 0 0 34px 0;
  font-weight: 400;
`;

export const StyledTabBar = styled.div`
  display: flex;
  width: 100%;
  max-width: 70%;
  background: #f1f5f9;
  border-radius: 8px;
  overflow: visible;
  margin: 0 auto 24px auto;
  padding: 4px 6px;
  box-shadow: none;
  align-items: center;
`;

export const StyledTab = styled.button<{ $active?: boolean }>`
  flex: 1 1 0;
  min-width: 0;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 28px;
  background: ${({ $active }) => ($active ? '#fff' : 'transparent')};
  color: ${({ $active }) => ($active ? '#181c32' : '#7c8597')};
  font-weight: ${({ $active }) => ($active ? 600 : 400)};
  font-size: 0.8rem;
  border: none;
  outline: none;
  cursor: pointer;
  border-radius: 8px;
  margin: 0 2px;
  box-shadow: none;
  z-index: ${({ $active }) => ($active ? 2 : 1)};
  transition:
    background 0.15s,
    color 0.15s;
`;

export const StyledCodeBlock = styled.pre`
  background: #111726;
  color: #4ade80;
  font-family: 'Fira Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  font-weight: 500;
  border-radius: 14px;
  padding: 32px 36px 28px 36px;
  margin: 0 auto 38px auto;
  min-width: 0;
  max-width: 70%;
  width: 100%;
  box-shadow: 0 8px 32px rgba(80, 80, 180, 0.11);
  display: block;
  overflow-x: auto;
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  @media (max-width: 900px) {
    max-width: 100%;
    padding: 22px 8px 20px 8px;
  }
`;

export const StyledCardGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 28px;
  margin: 38px auto 0 auto;
  max-width: 98%;
  width: 100%;
  @media (max-width: 1100px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
  }
  @media (max-width: 700px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
`;

// export const StyledDevCard = styled.div`
//   background: #fff;
//   border-radius: 16px;
//   box-shadow: 0 2px 16px rgba(80,80,180,0.06);
//   padding: 28px 22px 22px 22px;
//   display: flex;
//   flex-direction: column;
//   align-items: center;
//   min-width: 170px;
//   min-height: 150px;
//   border: 2px solid ${({ highlight }) => highlight || 'transparent'};
//   transition: border 0.18s;
// `;

export const StyledDevCard = styled.div<{ $highlight?: string }>`
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 16px rgba(80, 80, 180, 0.06);
  padding: 28px 22px 22px 22px;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 170px;
  min-height: 150px;
  border: 2px solid #f3f4f6;
  transition: border 0.18s;
  &:hover {
    border-color: ${({ $highlight }) => $highlight || 'transparent'};
  }
`;

export const StyledCardIcon = styled.div<{ $color?: string }>`
  font-size: 2.1rem;
  margin-bottom: 10px;
  color: ${({ $color }) => $color || '#7d5fff'};
`;

export const StyledCardTitle = styled.div`
  font-size: 1.09rem;
  font-weight: 600;
  margin-bottom: 13px;
  color: #23263b;
  display: flex;
  align-items: center;
  gap: 7px;
`;

export const StyledCardPills = styled.div`
  display: flex;
  flex-wrap: wrap;
  margin-top: 20px;
  gap: 2px;
`;

export const StyledCardPill = styled.div<{ $bg?: string }>`
  background: ${({ $bg }) => $bg || '#f6f7fb'};
  color: #23263b;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 7px;
  padding: 2.5px 11px;
  margin-bottom: 3px;
  display: inline-block;
  // margin: 0 0 20px 0;
  overflow-x: auto;
`;
