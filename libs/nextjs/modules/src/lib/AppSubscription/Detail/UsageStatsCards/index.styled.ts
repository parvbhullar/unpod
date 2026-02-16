import styled from 'styled-components';
import { Typography } from 'antd';

const { Text } = Typography;

export const StyledSection = styled.div``;

export const StyledHeading = styled(Typography.Title)`
  && {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 16px;
  }
`;

export const StyledMetricContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
`;

export const StyledLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

export const StyledName = styled(Text)`
  && {
    color: #555;
    font-size: 16px;
    font-weight: 500;
  }
`;

export const StyledMetricValue = styled.span`
  font-size: 20px;
  font-weight: 600;
`;

export const StyledValueWrapper = styled.div`
  margin-top: 8px;
`;

export const StyledSubText = styled(Text)`
  && {
    color: #888;
    font-size: 13px;
  }
`;
