import styled from 'styled-components';
import { Avatar } from 'antd';

export const StyledCardWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
`;

export const StyledAvatar = styled(Avatar)`
  background: ${({ theme }) => theme.palette.background.component};
  color: ${({ theme }) => theme.palette.success} !important;
`;

export const StyledSectionTitle = styled.div`
  font-size: 22px;
  font-weight: 700;
  text-align: center;
`;

export const StyledSubTitle = styled.div`
  font-size: 14px;
  color: #6b7280;
  text-align: center;
`;

export const StyledDetailsCard = styled.div`
  width: 100%;
  border-radius: 12px;
  padding: 18px 20px;
  margin-top: 10px;
  border: 1px solid ${({ theme }) => theme.border.color};
`;

export const StyledDetailsRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }
`;

export const StyledTextWrapper = styled.div`
  width: 600px;
  display: flex;
  justify-content: flex-end;
`;
