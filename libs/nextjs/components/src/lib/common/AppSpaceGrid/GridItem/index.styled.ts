import styled from 'styled-components';

export const EvalButtonWrapper = styled.div`
  display: none;
`;

export const StyledRoot = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1.5px solid #ececec;
  border-radius: 10px;
  box-shadow: 0 4px 16px 0 rgba(138, 119, 255, 0.1);
  padding: 18px 18px 16px;
  cursor: pointer;
  gap: 12px;
  transition:
    box-shadow 0.2s,
    border-color 0.2s;

  &:hover {
    box-shadow: 0 6px 24px 0 rgba(138, 119, 255, 0.18);
    border-color: #d1c4e9;

    ${EvalButtonWrapper} {
      display: flex;
    }
  }
`;

export const StyledDescription = styled.p`
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
`;
export const StyledTitleWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-bottom: 4px;

  .title {
    color: #28272aff;
    font-weight: 600;
    font-size: 1.08rem;
    margin-bottom: 0;
  }
`;

export const StyledTypeLabel = styled.span<{ $color?: string; $bg?: string }>`
  display: inline-block;
  padding: 2px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  color: ${({ $color }) => $color};
  background: ${({ $bg }) => $bg};
  margin-bottom: 2px;
`;

export const StyledContent = styled.div<{ $iconColor?: string }>`
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  a svg,
  .icon {
    font-size: 2rem;
    color: ${({ $iconColor }) => $iconColor || '#8a77ff'};
  }
`;

export const StyledHubRow = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: space-between;

  .ant-typography {
    margin-bottom: 0;
    font-size: 0.98rem;
  }
`;

export const StyledOrganizationContainer = styled.div`
  display: flex;
  align-items: center;
`;

export const StyledIconCircle = styled.div<{ $bg?: string }>`
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${({ $bg }) => $bg || '#f6e7ff'};
  border-radius: 30%;
  width: 34px;
  height: 34px;
`;
export const StyledDivider = styled.div`
  width: 100%;
  height: 1px;
  background: #d1cddbff;
  margin: 18px 0 10px 0;
`;
export const StyledPrivacyIcon = styled.div<{ $iconColor?: string }>`
  svg,
  .icon {
    font-size: 1rem;
    color: ${({ $iconColor }) => $iconColor || '#8a77ff'};
  }
`;
