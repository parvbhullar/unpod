import { Button, Flex, Form } from 'antd';
import styled from 'styled-components';

export const StylesImageWrapper = styled.div`
  position: relative;
  width: 90px;
  height: 90px;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 20px;
`;

export const StyleFormItemPrivacy = styled(Form.Item)`
  & .ant-form-item-explain-error {
    margin-top: 5px;
  }
`;

export const StyledMainContainer = styled.div`
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    width: 100%;
  }
`;

export const LogoContainer = styled(Flex)`
  flex-wrap: wrap;
  gap: 30px;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: center;
    gap: 0px;
  }
`;

export const StyledUploadButton = styled(Button)`
  border-radius: 6px;
  padding: 0 20px;
  height: 40px;

  @media (max-width: 768px) {
    width: 100%;
    justify-content: center;
    font-size: 13px;
    height: 36px;
  }

  @media (max-width: 480px) {
    font-size: 12px;
    height: 34px;
    padding: 0 12px;
  }
`;
