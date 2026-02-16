import styled from 'styled-components';

export const StyledUploadWrapper = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
`;

export const StyledUploadContainer = styled.div`
  position: relative;
`;

export const StyledInnerContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 10px;

  & .ant-typography {
    margin: 0;
  }
`;
