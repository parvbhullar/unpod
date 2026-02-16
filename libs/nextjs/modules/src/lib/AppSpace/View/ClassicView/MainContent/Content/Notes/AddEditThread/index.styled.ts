import styled from 'styled-components';
import { Divider, Input, Select, Upload } from 'antd';

const { Dragger } = Upload;

export const StyledContainer = styled.div`
  flex: 1;
  background-color: ${({ theme }) => theme.palette.background.default};
  /*width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto 0 auto;*/
`;

export const StyledDragger = styled(Dragger)`
  display: inline-flex;
  flex-direction: column;
  width: 100%;
  border-radius: 8px;

  .ant-upload-drag {
    border-width: 2px;
  }

  .ant-upload-btn {
    padding: 16px !important;
  }
`;

export const StyledMediaWrapper = styled.div`
  position: relative;
  margin: 0 0 20px 0;
`;

export const StyledIconWrapper = styled.div`
  cursor: pointer;
`;

export const StyledMediaList = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: ${({ theme }) => theme.radius.base}px;
  margin-bottom: 16px;
`;

export const StyledCoverWrapper = styled.div`
  position: relative;
  width: 100%;
  height: 130px;
  border-radius: ${({ theme }) => theme.radius.base}px;
  overflow: hidden;
`;

export const StyledDelContainer = styled.div`
  position: absolute;
  height: 22px;
  width: 22px;
  right: 10px;
  top: 10px;
  background-color: #ccc8c8;
  opacity: 0.75;
  border-radius: 50%;
  padding: 3px;
  cursor: pointer;

  .remove-cover-handle {
    color: ${({ theme }) => theme.palette.text.secondary};
    vertical-align: unset;
  }

  &:hover,
  ${StyledCoverWrapper}:hover ~ & {
    background-color: #868383 !important;
    opacity: 1 !important;

    .remove-cover-handle {
      color: ${({ theme }) => theme.palette.background.default};
      opacity: 1;
    }
  }
`;

export const StyledPostContainer = styled.div`
  display: flex;
  flex-direction: column;
  background-color: ${({ theme }) => theme.palette.background.default};
  padding: 16px 16px 0 16px;
  height: 100%;
  min-height: 100%;
`;

export const StyledActionBar = styled.div`
  position: sticky;
  bottom: 0;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-top: 1px solid ${({ theme }) => theme.border.color};
  padding: 16px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

export const StyledContent = styled.div`
  margin-top: 10px;
  font-size: 16px;
  line-height: 1.5;
`;

export const StyleExtraSpace = styled.div`
  flex: 1;
`;

export const StyledTitleInput = styled(Input)`
  font-size: 26px;
  font-weight: 600;
  padding: 4px 0;
  flex: 1;
`;

export const StyledTagsSelect = styled(Select)`
  padding: 4px 0;

  & .ant-select-selector {
    padding-inline-start: 0;
  }

  & .ant-select-selection-placeholder {
    font-weight: 500;
    color: ${({ theme }) => theme.palette.text.secondary};
    inset-inline-start: 0;
  }
`;

export const StyledTitleWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
`;

export const StyledDivider = styled(Divider)`
  margin: 6px 0;
`;
