import styled from 'styled-components';
import AppScrollbar from '../AppScrollbar';

export const StyledMailModalTextArea = styled.div`
  margin-top: 16px;
  position: relative;

  &.app-editor {
    height: calc(100% - 50px);
  }

  .ant-form-item.app-editor__form-item {
    margin-bottom: 0;
  }
`;

export const StyledAppScrollbar = styled(AppScrollbar)`
  height: ${({ visible }) =>
    visible ? 'calc(100% - 58px)' : 'calc(100% - 1px)'};
`;
