import styled from 'styled-components';
import { Button } from 'antd';
import { GlobalTheme } from '@unpod/constants';

export const WidgetContainer = styled.div`
  display: flex;
  align-items: center;
  padding: 1rem;
  gap: 1rem;
  width: 100%;
`;

export const Avatar = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid ${({ theme }: { theme: GlobalTheme }) => theme.border.color};

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`;

export const InfoSection = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
`;

export const StyledButton = styled(Button)`
  width: 100%;
  justify-content: center;
  align-items: center;
  border-radius: 12px !important;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  height: 51px !important;
`;
