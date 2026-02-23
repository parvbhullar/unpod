import styled from 'styled-components';

export const StyledRoot = styled.div`
  margin: 24px 0 0 0;
`;

export const IconWrapper = styled.span`
  cursor: pointer;
`;

export const StylesImageWrapper = styled.div`
  position: relative;
  width: 100px;
  height: 100px;
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: 50%;
  overflow: hidden;
  margin-bottom: 12px;
  cursor: pointer;
`;
