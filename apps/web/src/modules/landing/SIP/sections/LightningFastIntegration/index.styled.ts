import styled from 'styled-components';
import { Button, Typography } from 'antd';

const { Title, Paragraph } = Typography;

export const StyledBadge = styled.div`
  background: linear-gradient(to right, #514113, #5d4037);
  color: #ffca28 !important;
  padding: 6px 14px;
  border-radius: 20px;
  font-weight: bold;
  display: inline-block;
  font-size: 15px;
  margin-bottom: 20px;
  height: 37px;
  align-content: center;

  @media (max-width: 900px) {
    font-size: 12px;
  }
`;

export const StyledButton = styled(Button)`
  background: linear-gradient(to right, #ffc107, #ff5722);
  color: black !important;
  border: none;
  border-radius: 8px;
  padding: 0 24px;
  height: 44px;
  font-weight: 600;
  font-size: 16px;
  margin-top: 20px;

  &:hover {
    background: linear-gradient(to right, #ff5722, #ffc107) !important;
  }

  @media (max-width: 900px) {
    font-size: 14px;
    height: 40px;
    padding: 0 18px;
  }
`;

export const StyledChartWrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 30px;
  gap: 20px;
  width: 100%;

  @media (max-width: 900px) {
    flex-direction: row; /* Keep them side-by-side */
    align-items: flex-start;
    gap: 24px;
  }

  .chart-column {
    width: 48%;
    display: flex;
    justify-content: center;
    position: relative;

    @media (max-width: 900px) {
      width: 45%;
    }
  }
`;

export const StyledChartColumn = styled.div`
  position: relative;
  width: 40%;
  min-height: 400px;
  z-index: 2;

  @media (max-width: 900px) {
    width: 100%;
    min-height: 318px;
  }
`;

export const StyledLine = styled.div<{ $height?: string; $color?: string }>`
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: ${({ $height }) => $height || '60px'};
  background-color: ${({ $color }) => $color};

  @media (max-width: 900px) {
    height: ${({ $height }) => $height || '120px'};
  }
`;

export const StyledDot = styled.div<{ $top?: string; $color?: string }>`
  position: absolute;
  top: ${({ $top }) => $top || '0px'};
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: ${({ $color }) => $color};
  border-radius: 50%;
  width: 14px;
  height: 14px;
  z-index: 3;

  @media (max-width: 900px) {
    width: 10px;
    height: 10px;
  }
`;

export const StyledIconCircle = styled.div<{
  $top?: string;
  $fill?: string;
  $border?: string;
}>`
  position: absolute;
  top: ${({ $top }) => $top || '0px'};
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: ${({ $fill }) => $fill || 'transparent'};
  border: 2px solid ${({ $border }) => $border};
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${({ $border }) => $border};
  z-index: 3;
  font-size: 12px;

  @media (max-width: 900px) {
    width: 16px;
    height: 16px;
    font-size: 10px;
  }
`;

export const StyledLabel = styled.div<{
  $top?: string;
  $left?: string;
  $color?: string;
}>`
  position: absolute;
  top: ${({ $top }) => $top || '0px'};
  left: ${({ $left }) => $left || 'calc(50% + 20px)'};
  transform: translateY(-50%);
  font-size: 14px;
  font-weight: 600;
  color: ${({ $color }) => $color};

  @media (max-width: 900px) {
    font-size: 13px;
  }
`;

export const StyledLabelLeft = styled.div<{
  $top?: string;
  $left?: string;
  $color?: string;
}>`
  position: absolute;
  top: ${({ $top }) => $top || '0px'};
  left: ${({ $left }) => $left || 'calc(50% - 30px)'};
  transform: translateY(-50%);
  font-size: 17px;
  font-weight: 600;
  color: ${({ $color }) => $color};

  @media (max-width: 900px) {
    font-size: 13px;
  }
`;

export const StyledLabelRight = styled.div<{
  $top?: string;
  $left?: string;
  $color?: string;
}>`
  position: absolute;
  top: ${({ $top }) => $top || '0px'};
  left: ${({ $left }) => $left || 'calc(50% - 30px)'};
  transform: translateY(-50%);
  font-size: 17px;
  font-weight: 600;
  color: ${({ $color }) => $color};

  @media (max-width: 900px) {
    font-size: 13px;
    left: ${({ $left }) => $left || '5px'};
  }
`;

export const StyledSubText = styled.div<{ $top?: string; $left?: string }>`
  position: absolute;
  top: ${({ $top }) => $top || '0px'};
  left: ${({ $left }) => $left || 'calc(50% + 20px)'};
  transform: translateY(0);
  font-size: 13px;
  color: #b0b0b0;
  line-height: 1.3;

  @media (max-width: 900px) {
    font-size: 12px;
  }
`;

export const StyledCenterTime = styled.div`
  position: absolute;
  top: 180px;
  left: 58%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #a0a0a0;
  font-size: 14px;
  gap: 6px;
  z-index: 3;

  .icon {
    font-size: 18px;
    color: #a0a0a0;
  }

  .label {
    font-size: 14px;
    color: #a0a0a0;
    text-align: center;
  }

  @media (max-width: 900px) {
    position: absolute;
    bottom: -155px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 13px;

    .label {
      font-size: 13px;
      white-space: nowrap;
    }
  }
`;

export const StyledDividerLine = styled.div`
  width: 100%;
  height: 1px;
  background-color: #2f3545;
  margin-top: 175px;
`;

export const StyledStatsWrapper = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 90px;
  flex-wrap: wrap;
  gap: 20px;

  @media (max-width: 900px) {
    flex-direction: column;
    align-items: center;
    margin-top: 40px;
    gap: 16px;
  }
`;

export const StyledStatBox = styled.div`
  text-align: center;
  flex: 1;
  min-width: 150px;

  .value {
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 8px;
    color: #f8aa00;

    @media (max-width: 900px) {
      font-size: 26px;
    }
  }

  .label {
    font-size: 16px;
    color: #dcdcdc;

    @media (max-width: 900px) {
      font-size: 14px;
    }
  }

  &:nth-child(2) .value {
    color: #00d25b;
  }

  &:nth-child(3) .value {
    color: #3b9eff;
  }
`;

export const StyledHeading = styled(Title)`
  && {
    color: white;
    margin-top: 10px;
    font-size: 50px;

    @media (max-width: 900px) {
      font-size: 32px;
      margin-top: 12px;
    }
  }
`;

export const StyledParagraph = styled(Paragraph)`
  && {
    color: #dcdcdc;
    font-size: 18px;

    @media (max-width: 900px) {
      font-size: 15px;
    }
  }
`;
