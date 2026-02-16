import styled from 'styled-components';
import { Button } from 'antd';

export const WidgetContainer = styled.div`
  display: flex;
  align-items: center;
  background: white;
  padding: 1rem;
  gap: 1rem;
  width: 100%;
`;

export const Avatar = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #ccc;

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

export const Label = styled.div`
  font-size: 14px;
  font-weight: 500;
  color: #000;
`;

export const StyledButton = styled(Button)`
  width: 100%;
  justify-content: center;
  align-items: center;
  margin: 20px 0;
  border-radius: 12px !important;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  height: 51px !important;
`;

