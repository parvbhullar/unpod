import styled from 'styled-components';
import {Space} from 'antd';

export const StyledSpace = styled(Space)`
  display: flex;
  border-radius: 4px;
  padding: ${({theme}) => theme.space.sm} ${({theme}) => theme.space.md};
  border: 1px solid ${({theme}) => theme.border.color};
  margin-bottom: 12px;
  cursor: pointer;
`;

export const StyledPopoverWrapper = styled.div`
  min-width: 440px;
`;

export const StyledFormContainer = styled.div`
  display: flex;
  gap: 8px;
  & > :first-child {
    flex: 1; /* email input stretches */
  }

  & > :nth-child(2) {
    flex: 0 0 100px; /* role select fixed 100px */
  }

  & > :nth-child(3) {
    flex-shrink: 0; /* button stays natural size */
  }
`;

export const StyledRequestedMembersWrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

export const StyledRequestedMember = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 10px;

  .ant-avatar {
    margin-right: 10px;
  }
  .anticon {
    margin-left: 10px;
    transition: all 0.4s ease-in-out;
  }
  .bold {
    font-weight: bold;
  }
`;

export const StyledRequestedAccessWrapper = styled.div`
  display: flex;
  flex-direction: column;

  & > .ant-row {
    margin-bottom: 10px;
  }
`;
