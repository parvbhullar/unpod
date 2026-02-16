'use client';
import styled from 'styled-components';
import { Typography } from 'antd';

const { Paragraph } = Typography;
export const StyledRoot = styled.div`
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  text-align: center;
  background-color: rgba(58, 58, 58, 0.55);
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  color: ${({ theme }) => theme.palette.common.white}
  height: 100%;
  min-height: 160px;
  transition: background-color 0.3s;

  &:hover {
    background-color: rgba(58, 58, 58, 0.95);
  }
`;

export const StyledContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  color: ${({ theme }) => theme.palette.common.white};

  & .item-description {
    color: rgba(236, 236, 236, 0.96);
    margin-bottom: 0 !important;
  }
`;

export const StyledTitle = styled.div`
  font-size: 18px;
  line-height: 1.5;
  color: ${({ theme }) => theme.palette.common.white};
`;

export const StyledIconBox = styled.div`
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  border: 2px solid ${({ theme }) => theme.palette.primary};
  display: inline-flex;
  justify-content: center;
  align-self: center;
`;

export const StyledIconWrapper = styled.div`
  padding: 5px;
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  color: ${({ theme }) => theme.palette.common.white};
`;

export const StyledParagraph = styled(Paragraph)`
  flex: 1;
`;
