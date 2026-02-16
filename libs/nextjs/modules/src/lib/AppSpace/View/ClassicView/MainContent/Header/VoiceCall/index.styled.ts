import styled from 'styled-components';
import { Typography } from 'antd';

const { Paragraph } = Typography;

export const StyledRoot = styled.div`
  padding: 0;
  min-width: 500px;

  @media (max-width: 768px) {
    min-width: 400px;
  }

  @media (max-width: 500px) {
    min-width: 100%;
  }
`;

export const StyledItemRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
`;

export const StyledLabel = styled(Paragraph)`
  margin-bottom: 8px !important;
`;

export const StyledBottomBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 12px;
`;
