import styled from 'styled-components';

export const StyledContainer = styled.div`
  padding: 30px;
  width: 100%;
  max-width: 530px;
  margin: 0 auto;
`;

export const StyledInfoWrapper = styled.div`
  text-align: center;
  margin-bottom: 20px;
`;

export const StylesImageWrapper = styled.div`
  position: relative;
  width: 110px;
  height: 110px;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto 20px;
`;
