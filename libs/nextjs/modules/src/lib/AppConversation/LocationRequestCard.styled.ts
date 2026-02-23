import styled, {css, keyframes} from 'styled-components';

type StatusProps = {
  $success?: boolean;
  $declined?: boolean;
  $loading?: boolean;
};

export const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

export const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
`;

export const LocationRequestCard = styled.div`
  background: ${(props) => props.theme.palette.background.paper};
  border: 1px solid
    ${(props) => props.theme.border.color || 'rgba(0, 0, 0, 0.08)'};
  border-radius: 16px;
  padding: 24px;
  max-width: 480px;
`;

export const RequestHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
`;

export const LocationIcon = styled.div<StatusProps>`
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: ${(props) =>
  props.$success
    ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
    : props.$declined
      ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
      : props.theme.palette.primary
        ? `linear-gradient(135deg, ${props.theme.palette.primary} 0%, ${props.theme.palette.primary}dd 100%)`
        : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 22px;
  box-shadow: 0 2px 8px
    ${(props) =>
  props.$success
    ? 'rgba(16, 185, 129, 0.25)'
    : props.$declined
      ? 'rgba(239, 68, 68, 0.25)'
      : props.theme.palette.primary
        ? `${props.theme.palette.primary}30`
        : 'rgba(99, 102, 241, 0.25)'};
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  ${(props) =>
  props.$loading &&
  css`
      animation: ${pulse} 1.5s ease-in-out infinite;
    `}

  &:hover {
    transform: scale(1.05);
  }
`;

export const RequestContent = styled.div`
  flex: 1;
`;

export const RequestTitle = styled.div`
  font-weight: ${(props) => props.theme.font?.weight?.semiBold || 600};
  font-size: ${(props) => props.theme.font?.size?.base || '16px'};
  color: ${(props) =>
  props.theme.palette.text.primary || 'rgba(0, 0, 0, 0.88)'};
  margin-bottom: 4px;
  letter-spacing: -0.01em;
  line-height: 1.4;
`;

export const RequestSubtitle = styled.div`
  font-size: ${(props) => props.theme.font?.size?.sm || '13px'};
  color: ${(props) =>
  props.theme.palette.text.secondary || 'rgba(0, 0, 0, 0.6)'};
  font-weight: ${(props) => props.theme.font?.weight?.medium || 500};
  line-height: 1.4;
`;

export const RequestReason = styled.div`
  font-size: ${(props) => props.theme.font?.size?.sm || '14px'};
  color: ${(props) =>
  props.theme.palette.text.secondary || 'rgba(0, 0, 0, 0.65)'};
  line-height: 1.6;
  margin-bottom: 20px;
  padding: 14px 16px;
  background: ${(props) =>
  props.theme.palette.background?.default || 'rgba(0, 0, 0, 0.02)'};
  border-radius: 10px;
  border-left: 3px solid
    ${(props) => props.theme.palette.primary || '#6366f1'}40;
`;

export const ButtonContainer = styled.div`
  display: flex;
  gap: 12px;
  margin-top: 16px;
`;

export const StatusContainer = styled.div<StatusProps>`
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px;
  border-radius: 12px;
  margin-top: 16px;
  background: ${(props) =>
  props.$success
    ? 'rgba(16, 185, 129, 0.08)'
    : props.$declined
      ? 'rgba(239, 68, 68, 0.08)'
      : props.theme.palette.primary
        ? `${props.theme.palette.primary}10`
        : 'rgba(99, 102, 241, 0.08)'};
  border: 1px solid
    ${(props) =>
  props.$success
    ? 'rgba(16, 185, 129, 0.2)'
    : props.$declined
      ? 'rgba(239, 68, 68, 0.2)'
      : props.theme.palette.primary
        ? `${props.theme.palette.primary}20`
        : 'rgba(99, 102, 241, 0.2)'};
  animation: ${fadeIn} 0.3s ease-out;
`;

export const StatusIcon = styled.div<StatusProps>`
  font-size: 22px;
  color: ${(props) =>
  props.$success
    ? '#10b981'
    : props.$declined
      ? '#ef4444'
      : props.theme.palette.primary || '#6366f1'};
  display: flex;
  align-items: center;
  margin-top: 2px;
`;

export const StatusText = styled.div<StatusProps>`
  flex: 1;
  font-size: ${(props) => props.theme.font?.size?.sm || '14px'};
  font-weight: ${(props) => props.theme.font?.weight?.medium || 500};
  color: ${(props) =>
  props.$success
    ? '#059669'
    : props.$declined
      ? '#dc2626'
      : props.theme.palette.text.secondary || 'rgba(0, 0, 0, 0.65)'};
  line-height: 1.5;
`;

export const LocationCoords = styled.div`
  font-size: ${(props) => props.theme.font?.size?.sm || '12px'};
  color: ${(props) =>
  props.theme.palette.text.secondary || 'rgba(0, 0, 0, 0.6)'};
  font-family: ${(props) =>
  props.theme.font?.family ||
  "'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Roboto Mono', monospace"};
  margin-top: 6px;
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 6px;
  display: inline-block;
  font-weight: ${(props) => props.theme.font?.weight?.medium || 500};
`;
