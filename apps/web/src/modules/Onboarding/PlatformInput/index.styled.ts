'use client';
import styled from 'styled-components';

export const StyledInputWrapper = styled.div`
  border-radius: 8px;
  border: 1px solid ${(props) => props.theme.border.color} !important;
  padding: 12px;
  display: flex;
  flex-direction: column;
  width: 600px;
  margin: 24px auto 0 auto;
`;
