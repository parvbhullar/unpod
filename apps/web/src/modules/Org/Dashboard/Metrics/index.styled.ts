import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledSection = styled.div`
  margin-bottom: 24px;
`;

export const StyledHeading = styled(Typography.Title)`
  && {
    font-size: 20px;
    margin-bottom: 16px;
    margin-top: 20px;
  }
`;

export const StyledCard = styled.div`
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
`;

export const StyledValueRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
`;

export const StyledMetricValue = styled.div`
  font-size: 24px;
  font-weight: 600;
`;

export const StyledChange = styled.div`
  display: flex;
  align-items: center;
  color: ${(props) => props.color};
  font-weight: 500;
  gap: 4px;
`;
