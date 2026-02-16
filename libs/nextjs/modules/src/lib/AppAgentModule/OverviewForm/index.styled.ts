import styled from 'styled-components';
import { Button, Flex, Form } from 'antd';

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

export const LogoContainer = styled(Flex)`
  flex-wrap: wrap;
  gap: 30px;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: center;
    gap: 0;
  }
`;

export const StyledUploadButton = styled(Button)`
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

export const TagWrapper = styled.div`
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 52}px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    grid-template-columns: repeat(1, minmax(0, 1fr)) !important;
  }
`;

export const TonePersonalityContainer = styled.div`
  margin-bottom: 12px;
`;
