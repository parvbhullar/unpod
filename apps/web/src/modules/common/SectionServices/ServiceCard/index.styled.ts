import styled from 'styled-components';
import { Typography } from 'antd';

const { Paragraph } = Typography;

export const StyledContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  color: ${({ theme }) => theme.palette.common.white};
  text-align: center;

  & .item-description {
    color: rgba(236, 236, 236, 0.96);
    margin-bottom: 0 !important;
  }
`;

export const StyledTitle = styled.div`
  font-size: 21px;
  color: ${({ theme }) => theme.palette.common.white};
`;

export const StyledIconBox = styled.div`
  padding: 2px;
  display: inline-flex;
  justify-content: center;
  align-self: center;
  background-color: ${({ theme }) => theme.palette.warning};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  transition: background-color 0.3s;
`;

export const StyledIconWrapper = styled.div`
  padding: 5px;
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  background-color: ${({ theme }) => theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  transition: background-color 0.3s;
`;

export const StyledParagraph = styled(Paragraph)`
  flex: 1;
  font-size: 16px;
`;

export const StyledRoot = styled.div`
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background-color: ${({ theme }) => theme.palette.primary};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  color: ${({ theme }) => theme.palette.common.white}
  height: 100%;
  min-height: 160px;
  transition: background-color 0.3s;

  &:hover {
    background-color: ${({ theme }) => theme.palette.warning};

    ${StyledIconBox} {
      background-color: ${({ theme }) => theme.palette.primary};
    }

    ${StyledIconWrapper} {
      background-color: ${({ theme }) => theme.palette.warning};
    }
  }
`;
