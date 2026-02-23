'use client';
import styled from 'styled-components';
import {Card, Flex, Input, Typography} from 'antd';

const {Title, Text} = Typography;

export const StyledInputWrapper = styled.div`
  border-radius: 8px;
  display: flex;
  flex-direction: column !important;
  overflow: hidden;
`;

export const StyledItemWrapper = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  align-items: center;
`;

export const StyledText = styled(Text)`
  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    font-size: 11px !important;
  }
`;

export const StyledFlex = styled(Flex)`
  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    flex-direction: row;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    flex-direction: column;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    flex-direction: column;
  }
`;

export const Tip = styled(Title)`
  font-size: ${({theme}) => theme.font.size.sm} !important;
  font-weight: ${({theme}) => theme.font.weight.regular} !important;
  padding: 16px;
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: 12px;
  display: flex;
  gap: 4px;
`;

export const TipText = styled.span`
  display: flex;
  font-size: ${({theme}) => theme.font.size.sm} !important;
`;

export const CardWrapper = styled(Card)`
  border: 1px solid ${({theme}) => theme.border.color} !important;
  margin-bottom: 12px;

  .ant-card-body {
    padding: 12px 0 !important;
  }

  .ant-card-actions {
    padding: 12px;
    margin-top: -27px !important;
    border-top: 1px solid ${({theme}) => theme.border.color} !important;

    ul {
      margin: 0;
    }

    li {
      margin: 0 !important;
      padding: 0;
    }
  }

  &:hover {
    border: 1px solid ${({theme}) => theme.palette.primary} !important;
  }

  &:focus-within {
    border-color: ${({theme}) => theme.palette.primary} !important;
  }
`;

export const StyledTextArea = styled(Input.TextArea)`
  //border-radius: 12px 12px 0 0  !important;
  border: none !important;
  box-shadow: none !important;
  scrollbar-width: thin;
`;
