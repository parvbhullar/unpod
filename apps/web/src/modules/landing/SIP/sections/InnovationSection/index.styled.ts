import styled from 'styled-components';
import { Card } from 'antd';

export const StyledSection = styled.section`
  width: 100vw;
  min-height: 480px;
  background: Styled;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 64px 0 64px 0;
  box-sizing: border-box;
`;

export const StyledContentWrap = styled.div`
  display: flex;
  max-width: 1200px;
  width: 100%;
  gap: 52px;
  align-items: flex-start;
  justify-content: center;
  @media (max-width: 1000px) {
    flex-direction: column;
    gap: 36px;
    align-items: center;
  }
`;

export const StyledLeftCol = styled.div`
  flex: 1 1 360px;
  min-width: 320px;
  max-width: 470px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
`;

export const StyledPillTag = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #f4f7ff;
  color: #377dff;
  font-weight: 500;
  font-size: 15px;
  border-radius: 999px;
  padding: 6px 18px;
  margin-bottom: 18px;
  box-shadow: 0 2px 8px rgba(80, 80, 120, 0.04);
`;

export const StyledHeadline = styled.h2`
  font-size: 2.1rem;
  font-weight: 800;
  color: #181c32;
  margin-bottom: 0;
  line-height: 1.18;
`;

export const StyledHighlight = styled.span`
  color: #7d5fff;
  font-size: 2.1rem;
  font-weight: 800;
  margin-bottom: 0;
  display: inline;
`;

export const StyledSubtitle = styled.p`
  color: #464d61;
  font-size: 1.08rem;
  margin: 22px 0 0 0;
  font-weight: 400;
  letter-spacing: 0.01em;
`;

export const StyledChecklist = styled.ul`
  text-align: left;
  list-style: none;
  padding: 0;
  margin: 32px 0 0 0;
  li {
    margin-bottom: 16px;
    font-size: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #23263b;
  }
`;

export const StyledCTAButton = styled.button`
  background: #377dff;
  color: #fff;
  border: none;
  font-weight: 600;
  font-size: 1.05rem;
  padding: 11px 28px;
  margin-top: 26px;
  box-shadow: 0 2px 8px rgba(80, 80, 120, 0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.18s;
  &:hover {
    background: #2156c8;
  }
`;

export const StyledRightCol = styled.div`
  flex: 1 1 400px;
  min-width: 340px;
  max-width: 520px;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

export const StyledCodeCard = styled.div`
  background: #181e2a;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(80, 80, 180, 0.1);
  padding: 0 0 0 0;
  width: 100%;
  // max-width: 430px;
  min-width: 320px;
  margin-bottom: 20px;
  overflow: hidden;
`;

export const StyledCodeHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 16px 0 0 18px;
  height: 34px;
`;

export const StyledCodeDot = styled.span<{ $color?: string }>`
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
  background: ${({ $color }) => $color || '#bbb'};
`;

export const StyledCodeBlock = styled.pre`
  background: none;
  width: 100%;
  color: #4ade80;
  font-family: 'Fira Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  padding: 20px 22px 18px 22px;
  border-radius: 0 0 18px 18px;
  margin: 0;
  overflow-x: auto;
`;

export const StyledStatRow = styled.div`
  display: flex;
  gap: 18px;
  width: 100%;
  justify-content: center;
  margin-top: 6px;
`;

export const StyledStatCard = styled(Card)<{ $bg?: string }>`
  border-radius: 12px !important;
  background: ${({ $bg }) => $bg || '#f6f7fb'} !important;
  box-shadow: 0 2px 16px rgba(80, 80, 180, 0.06);
  border: none;
  // min-width: 180px;
  flex: 1 1 0%;
  min-height: 92px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  .ant-card-body {
    padding: 18px 0 10px 0 !important;
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
`;

export const StyledCardWrapper = styled.div`
  background: #fff;
  border-radius: 12px;
  box-shadow:
    0 18px 48px 0 rgba(80, 80, 180, 0.13),
    0 0 80px 0 #e5eaff;
  padding: 16px;
  max-width: 700px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: visible;
  border: none;
`;
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
  font-weight: 700;
  margin-bottom: 13px;
  color: #23263b;
  display: flex;
  align-items: center;
  gap: 7px;
`;

export const StyledCardPills = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
`;

export const StyledCardPill = styled.div<{ $bg?: string }>`
  background: ${({ $bg }) => $bg || '#f6f7fb'};
  color: #23263b;
  font-size: 0.91rem;
  font-weight: 500;
  border-radius: 7px;
  padding: 2.5px 11px;
  margin-bottom: 3px;
  display: inline-block;
  overflow-x: auto;
`;

export const StyledStatValue = styled.div<{ $color?: string }>`
  color: ${({ $color }) => $color || '#377dff'};
  font-weight: 700;
  font-size: 1.3rem;
  margin-bottom: 2px;
`;

export const StyledStatLabel = styled.div<{ $color?: string }>`
  color: ${({ $color }) => $color || '#377dff'};
  font-size: 1.04rem;
  font-weight: 600;
`;

export const StyledCodeLine = styled.span`
  display: block;
  white-space: pre;
  font-family: inherit;
  font-size: inherit;
  line-height: 1.8;
`;
