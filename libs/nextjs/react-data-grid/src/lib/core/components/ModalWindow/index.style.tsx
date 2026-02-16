import styled from 'styled-components';
import { Modal } from 'antd';

export const StyledModal = styled(Modal)`
  & .ant-modal-header {
    padding: 20px 24px 0;
  }

  & .ant-modal-content {
    padding: 0;
  }
`;
