import styled from 'styled-components';
import { Typography, Upload } from 'antd';

const { Paragraph } = Typography;
const { Dragger } = Upload;

export const StyledRoot = styled.div`
  flex: 1;
`;

export const StyledContainer = styled.div`
  padding: 16px;
`;

export const StyledDragger = styled(Dragger)`
  display: inline-flex;
  flex-direction: column;
  width: 100%;
  border-radius: 8px;
  margin-bottom: 16px;

  .ant-upload-drag {
    border-width: 2px;
  }

  .ant-upload-btn {
    padding: 16px !important;
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

export const StyledActions = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;
