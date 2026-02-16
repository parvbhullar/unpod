import styled from 'styled-components';
import { Button, Input } from 'antd';

const { TextArea } = Input;

type MessageBubbleContainerProps = {
  $isUser?: boolean;
  $isFirstInGroup?: boolean;
  $isLastInGroup?: boolean;
};

type UserAvatarProps = {
  $color?: string;
};

type MessageWrapperProps = {
  $isUser?: boolean;
};

type MessageContentProps = {
  $isUser?: boolean;
};

type MessageMetaProps = {
  $isUser?: boolean;
};

type ScrollShadowProps = {
  $showLeftShadow?: boolean;
  $showRightShadow?: boolean;
};

type BadgeProps = {
  $variant?: 'success' | 'warning' | string;
};

type CallIconWrapperProps = {
  $status?: string;
};

type ChatSendButtonProps = {
  $hasContent?: boolean;
};

export const ConversationContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: calc(100vh - 74px);
  width: 100%;
  background: ${({ theme }) => theme.palette.background.default};
`;

export const ConversationHeader = styled.div`
  flex-shrink: 0;
  padding: ${({ theme }) => theme.space.md} ${({ theme }) => theme.space.lg};
  border-bottom: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  background: ${({ theme }) => theme.palette.background.paper};
`;

export const ConversationMessages = styled.div`
  flex: 1;
  overflow-y: auto;
  overflow-x: visible;
  padding: ${({ theme }) => theme.space.lg} ${({ theme }) => theme.space.xl};

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.border.color};
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
`;

export const ConversationMessagesInner = styled.div`
  max-width: ${({ theme }) => theme.sizes.mainContentWidth};
  margin: 0 auto;
  width: 100%;
  position: relative;
`;

export const ConversationInput = styled.div`
  position: sticky;
  bottom: 0;
  flex-shrink: 0;
  padding: ${({ theme }) => theme.space.md} ${({ theme }) => theme.space.lg};
  border-top: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  background: ${({ theme }) => theme.palette.background.paper};
  z-index: 10;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: ${({ theme }) => theme.space.sm} 0;
  }
`;

export const MessageBubbleContainer = styled.div<MessageBubbleContainerProps>`
  display: flex;
  gap: ${({ theme }) => theme.space.sm};
  margin-bottom: ${({ $isLastInGroup, theme }) =>
    $isLastInGroup ? theme.space.lg : theme.space.xs};
  justify-content: ${({ $isUser }) => ($isUser ? 'flex-end' : 'flex-start')};
  align-items: flex-start;
`;

export const UserAvatar = styled.div<UserAvatarProps>`
  width: 36px;
  height: 36px;
  border-radius: ${({ theme }) => theme.radius.circle};
  background: ${({ $color, theme }) => $color || theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  font-size: ${({ theme }) => theme.font.size.base};
  flex-shrink: 0;
`;

export const MessageWrapper = styled.div<MessageWrapperProps>`
  ${({ $isUser, theme }) =>
    $isUser
      ? `
    background: linear-gradient(90deg, rgba(138, 119, 255, 0.14) 50%, rgba(245, 136, 255, 0.14) 100%);
    padding: 10px ${theme.space.md};
    border-radius: 12px;
    border-bottom-right-radius: 4px;
    width: fit-content;
    max-width: 700px;
    min-width: 60px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    transition: all 0.2s ease;

    &:hover {
      background: linear-gradient(90deg, rgba(138, 119, 255, 0.2) 50%, rgba(245, 136, 255, 0.2) 100%);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
  `
      : `
    background: transparent;
    padding: 0;
    border-radius: 0;
    width: 100%;
    max-width: none;
    box-shadow: none;
  `}
`;

export const MessageContent = styled.div<MessageContentProps>`
  color: ${({ theme }) => theme.palette.text.primary};
  word-wrap: break-word;
  line-height: 1.5;
  font-size: ${({ theme }) => theme.font.size.base};
  position: relative;
  overflow-wrap: break-word;

  /* Style for markdown content */
  > div {
    /* Reset first/last margins */
    > *:first-child {
      margin-top: 0 !important;
    }

    > *:last-child {
      margin-bottom: 0 !important;
    }
  }

  /* Code block styling */
  pre {
    margin: 12px 0;
    border-radius: 8px;
    overflow: hidden;
  }

  /* Inline code styling */
  code {
    font-family:
      'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Droid Sans Mono',
      'Source Code Pro', monospace;
  }

  /* Link styling */
  a {
    word-break: break-all;

    &:hover {
      text-decoration: underline;
      opacity: 0.9;
    }
  }

  /* Strong/bold text */
  strong {
    font-weight: 600;
  }

  /* Emphasis/italic text */
  em {
    font-style: italic;
  }

  /* Horizontal rule */
  hr {
    border: none;
    border-top: 1px solid
      ${({ $isUser }) =>
        $isUser ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.1)'};
    margin: 16px 0;
  }
`;

export const MessageMeta = styled.div<MessageMetaProps>`
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  margin-top: ${({ theme }) => theme.space.xss};
  padding: 0 ${({ theme }) => theme.space.xss};
  text-align: ${({ $isUser }) => ($isUser ? 'right' : 'left')};
  width: 100%;
  display: block;
`;

export const InputContainer = styled.div`
  max-width: ${({ theme }) => theme.sizes.mainContentWidth};
  margin: 0 auto;
  width: 100%;
  display: flex;
  gap: ${({ theme }) => theme.space.sm};
  align-items: flex-end;
`;

export const InputBox = styled.textarea`
  flex: 1;
  resize: none;
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: ${({ theme }) => theme.space.sm} ${({ theme }) => theme.space.md};
  font-size: ${({ theme }) => theme.font.size.base};
  font-family: ${({ theme }) => theme.font.family};
  line-height: 1.5;
  max-height: 200px;
  min-height: ${({ theme }) => theme.heightRule.lg};
  background: ${({ theme }) => theme.palette.background.default};
  color: ${({ theme }) => theme.palette.text.primary};

  &:focus {
    outline: none;
    border-color: ${({ theme }) => theme.palette.primary};
  }

  &::placeholder {
    color: ${({ theme }) => theme.palette.text.secondary};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    background: ${({ theme }) => theme.palette.background.disabled};
  }
`;

export const SendButton = styled.button`
  background: ${({ theme, disabled }) =>
    disabled ? theme.border.color : theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  border: none;
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: ${({ theme }) => theme.space.sm} ${({ theme }) => theme.space.lg};
  font-size: ${({ theme }) => theme.font.size.base};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  transition: all 0.2s;
  min-height: ${({ theme }) => theme.heightRule.lg};

  &:hover {
    background: ${({ theme, disabled }) =>
      disabled ? theme.border.color : theme.palette.primaryActive};
  }

  &:active {
    transform: ${({ disabled }) => (disabled ? 'none' : 'scale(0.98)')};
  }
`;

/* Modern Chat Input Styles */
export const ChatInputWrapper = styled.div`
  max-width: ${({ theme }) => theme.sizes.mainContentWidth};
  margin: 0 auto;
  width: 100%;
  display: flex;
  align-items: flex-end;
  gap: ${({ theme }) => theme.space.sm};
  position: relative;
  background: ${({ theme }) => theme.palette.background.paper};
  border: 2px solid ${({ theme }) => theme.border.color};
  border-radius: 24px;
  padding: ${({ theme }) => theme.space.sm};
  transition: all 0.2s ease;

  &:focus-within {
    border-color: ${({ theme }) => theme.palette.primary};
    box-shadow: 0 0 0 3px ${({ theme }) => theme.palette.primary}15;
  }
`;

export const ChatInputBox = styled(TextArea)`
  flex: 1;
  resize: none;
  background: transparent !important;
  padding: 6px 8px;

  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  will-change: height, padding, margin;

  &::-webkit-scrollbar {
    display: none;
  }
`;

export const ChatSendButton = styled(Button)<ChatSendButtonProps>`
  width: 32px !important;
  height: 32px;
  min-width: 32px !important;
  border-radius: 50%;
  border: 1px solid ${({ theme }) => theme.border.color};
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  transition: all 0.2s ease;

  svg {
    margin-left: 3px;
  }
`;

export const ThinkingIndicator = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.space.sm};
  margin-bottom: ${({ theme }) => theme.space.lg};
  align-items: flex-start;
`;

export const ThinkingDots = styled.div`
  background: ${({ theme }) => theme.palette.background.paper};
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  padding: ${({ theme }) => theme.space.md} ${({ theme }) => theme.space.lg};
  border-radius: ${({ theme }) => theme.radius.base}px
    ${({ theme }) => theme.radius.base}px ${({ theme }) => theme.radius.base}px
    4px;
  display: flex;
  gap: 6px;

  span {
    width: 8px;
    height: 8px;
    border-radius: ${({ theme }) => theme.radius.circle};
    background: ${({ theme }) => theme.border.color};
    animation: bounce 1.4s infinite ease-in-out both;

    &:nth-child(1) {
      animation-delay: -0.32s;
    }

    &:nth-child(2) {
      animation-delay: -0.16s;
    }
  }

  @keyframes bounce {
    0%,
    80%,
    100% {
      transform: scale(0);
    }
    40% {
      transform: scale(1);
    }
  }
`;

export const LoadMoreButton = styled.button`
  margin: 0 auto ${({ theme }) => theme.space.lg};
  display: block;
  background: transparent;
  color: ${({ theme }) => theme.palette.primary};
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.palette.primary};
  border-radius: ${({ theme }) => theme.radius.sm}px;
  padding: ${({ theme }) => theme.space.xs} ${({ theme }) => theme.space.md};
  font-size: ${({ theme }) => theme.font.size.sm};
  font-weight: ${({ theme }) => theme.font.weight.medium};
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: ${({ theme }) => theme.palette.primary};
    color: ${({ theme }) => theme.palette.common.white};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

export const DateSeparator = styled.div`
  display: flex;
  align-items: center;
  margin: ${({ theme }) => theme.space.xl} 0 ${({ theme }) => theme.space.lg};
  gap: ${({ theme }) => theme.space.md};

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: ${({ theme }) => theme.border.color};
  }

  span {
    font-size: ${({ theme }) => theme.font.size.sm};
    font-weight: ${({ theme }) => theme.font.weight.semiBold};
    color: ${({ theme }) => theme.palette.text.secondary};
    white-space: nowrap;
    padding: ${({ theme }) => theme.space.xs} ${({ theme }) => theme.space.md};
    background: ${({ theme }) => theme.palette.background.paper};
    border-radius: ${({ theme }) => theme.radius.base}px;
    border: 1px solid ${({ theme }) => theme.border.color};
  }
`;

export const ProviderCardsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.md};
  width: 100%;
  overflow: visible;
`;

export const ProviderCardsScroll = styled.div<ScrollShadowProps>`
  display: flex;
  flex-wrap: nowrap;
  gap: ${({ theme }) => theme.space.md};
  overflow-x: auto;
  overflow-y: hidden;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  padding: ${({ theme }) => theme.space.sm} 0;
  -webkit-overflow-scrolling: touch;
  transition: box-shadow 0.3s ease;

  /* Conditional inset shadows like Ant Design */
  box-shadow: ${({ $showLeftShadow, $showRightShadow }) => {
    const shadows = [];
    if ($showLeftShadow) {
      shadows.push('inset 10px 0 8px -8px rgba(0, 0, 0, 0.08)');
    }
    if ($showRightShadow) {
      shadows.push('inset -10px 0 8px -8px rgba(0, 0, 0, 0.08)');
    }
    return shadows.length > 0 ? shadows.join(', ') : 'none';
  }};

  /* Show scrollbar for better UX */
  scrollbar-width: thin;
  scrollbar-color: ${({ theme }) => theme.palette.primary}40 transparent;

  &::-webkit-scrollbar {
    height: 8px;
  }

  &::-webkit-scrollbar-track {
    background: ${({ theme }) => theme.palette.background.default};
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.palette.primary}40;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: ${({ theme }) => theme.palette.primary}60;
  }
`;

export const ProviderCard = styled.div`
  background: ${({ theme }) => theme.palette.background.paper};
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: ${({ theme }) => theme.space.md};
  transition: all 0.2s;
  cursor: pointer;
  flex: 0 0 auto;
  width: 320px;
  min-width: 320px;
  scroll-snap-align: start;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 280px;
    min-width: 280px;
  }

  &:hover {
    border-color: ${({ theme }) => theme.palette.primary};
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

export const ProviderCardHeader = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.space.md};
  margin-bottom: ${({ theme }) => theme.space.sm};
`;

export const ProviderImage = styled.img`
  width: 80px;
  height: 80px;
  border-radius: ${({ theme }) => theme.radius.sm}px;
  object-fit: cover;
  flex-shrink: 0;
  background: ${({ theme }) => theme.palette.background.default};
`;

export const ProviderInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

export const ProviderName = styled.h3`
  margin: 0 0 ${({ theme }) => theme.space.xss};
  font-size: ${({ theme }) => theme.font.size.lg};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  color: ${({ theme }) => theme.palette.text.primary};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

export const ProviderDescription = styled.p`
  margin: 0 0 ${({ theme }) => theme.space.xs};
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
`;

export const ProviderRating = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xs};
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.primary};
`;

export const Star = styled.span`
  color: ${({ theme }) => theme.palette.warning || '#faad14'};
`;

export const ProviderDetails = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.xs};
  margin-top: ${({ theme }) => theme.space.sm};
  padding-top: ${({ theme }) => theme.space.sm};
  border-top: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
`;

export const ProviderDetailRow = styled.div`
  display: flex;
  align-items: flex-start;
  gap: ${({ theme }) => theme.space.xs};
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.primary};

  svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    margin-top: 2px;
    color: ${({ theme }) => theme.palette.text.secondary};
  }
`;

export const ProviderBadges = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.space.xs};
  flex-wrap: wrap;
  margin-top: ${({ theme }) => theme.space.xs};
`;

export const Badge = styled.span<BadgeProps>`
  display: inline-flex;
  align-items: center;
  padding: ${({ theme }) => theme.space.xss} ${({ theme }) => theme.space.xs};
  background: ${({ $variant, theme }) =>
    $variant === 'success'
      ? theme.palette.success || '#52c41a'
      : $variant === 'warning'
        ? theme.palette.warning || '#faad14'
        : theme.palette.background.default};
  color: ${({ theme }) => theme.palette.common.white};
  border-radius: ${({ theme }) => theme.radius.sm}px;
  font-size: ${({ theme }) => theme.font.size.sm};
  font-weight: ${({ theme }) => theme.font.weight.medium};
`;

export const ProviderQueryHeader = styled.div`
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  margin-bottom: ${({ theme }) => theme.space.sm};
  font-style: italic;
`;

export const WebCardsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.md};
  width: 100%;
  overflow: visible;
`;

export const WebCardsScroll = styled(ProviderCardsScroll)``;

export const WebCard = styled.div`
  background: ${({ theme }) => theme.palette.background.paper};
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  overflow: hidden;
  transition: all 0.2s;
  cursor: pointer;
  flex: 0 0 auto;
  width: 340px;
  min-width: 340px;
  scroll-snap-align: start;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 300px;
    min-width: 300px;
  }

  &:hover {
    border-color: ${({ theme }) => theme.palette.primary};
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

export const WebCardBanner = styled.img`
  width: 100%;
  height: 200px;
  object-fit: cover;
  background: ${({ theme }) => theme.palette.background.default};
`;

export const WebCardContent = styled.div`
  padding: ${({ theme }) => theme.space.md};
`;

export const WebCardTitle = styled.h3`
  margin: 0 0 ${({ theme }) => theme.space.xs};
  font-size: ${({ theme }) => theme.font.size.lg};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  color: ${({ theme }) => theme.palette.text.primary};
  line-height: 1.4;
`;

export const WebCardDescription = styled.p`
  margin: 0 0 ${({ theme }) => theme.space.md};
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

export const WebCardMeta = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: ${({ theme }) => theme.space.sm};
  align-items: center;
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  padding-top: ${({ theme }) => theme.space.sm};
  border-top: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
`;

export const WebCardSource = styled.span`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xss};
  font-weight: ${({ theme }) => theme.font.weight.medium};
  color: ${({ theme }) => theme.palette.primary};
`;

export const WebCardDivider = styled.span`
  color: ${({ theme }) => theme.border.color};
`;

export const WebCardDate = styled.span`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xss};
`;

export const WebCardScore = styled.span`
  display: inline-flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xss};
  padding: ${({ theme }) => theme.space.xss} ${({ theme }) => theme.space.xs};
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.radius.sm}px;
  font-weight: ${({ theme }) => theme.font.weight.medium};
  color: ${({ theme }) => theme.palette.text.primary};
`;

export const QueryHeader = styled.div`
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  margin-bottom: ${({ theme }) => theme.space.sm};
  font-style: italic;
`;

export const BookingCardsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.md};
  width: 100%;
  overflow: visible;
`;

export const BookingCardsScroll = styled(ProviderCardsScroll)``;

export const BookingCard = styled.div`
  background: ${({ theme }) => theme.palette.background.paper};
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  flex: 0 0 auto;
  width: 360px;
  min-width: 360px;
  scroll-snap-align: start;
  cursor: pointer;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 320px;
    min-width: 320px;
  }
  overflow: hidden;
  transition: all 0.2s;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

export const BookingCardHeader = styled.div<{ $status?: string }>`
  padding: ${({ theme }) => theme.space.md};
  background: ${({ $status, theme }) =>
    $status === 'confirmed'
      ? 'rgba(82, 196, 26, 0.1)'
      : $status === 'pending'
        ? 'rgba(250, 173, 20, 0.1)'
        : $status === 'cancelled'
          ? 'rgba(255, 77, 79, 0.1)'
          : theme.palette.background.default};
  border-bottom: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
`;

export const BookingHeaderTop = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: ${({ theme }) => theme.space.sm};
  margin-bottom: ${({ theme }) => theme.space.xs};
`;

export const BookingTitle = styled.h3`
  margin: 0;
  font-size: ${({ theme }) => theme.font.size.lg};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  color: ${({ theme }) => theme.palette.text.primary};
`;

export const BookingStatus = styled.span<{ $status?: string }>`
  display: inline-flex;
  align-items: center;
  padding: ${({ theme }) => theme.space.xss} ${({ theme }) => theme.space.sm};
  background: ${({ $status, theme }) =>
    $status === 'confirmed'
      ? theme.palette.success || '#52c41a'
      : $status === 'pending'
        ? theme.palette.warning || '#faad14'
        : $status === 'cancelled'
          ? theme.palette.error || '#ff4d4f'
          : theme.palette.background.default};
  color: ${({ theme }) => theme.palette.common.white};
  border-radius: ${({ theme }) => theme.radius.base}px;
  font-size: ${({ theme }) => theme.font.size.sm};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  text-transform: uppercase;
  flex-shrink: 0;
`;

export const BookingDescription = styled.p`
  margin: 0;
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
`;

export const BookingCardBody = styled.div`
  padding: ${({ theme }) => theme.space.md};
`;

export const BookingSection = styled.div`
  margin-bottom: ${({ theme }) => theme.space.md};

  &:last-child {
    margin-bottom: 0;
  }
`;

export const BookingSectionTitle = styled.h4`
  margin: 0 0 ${({ theme }) => theme.space.xs};
  font-size: ${({ theme }) => theme.font.size.sm};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  color: ${({ theme }) => theme.palette.text.primary};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

export const BookingInfoRow = styled.div`
  display: flex;
  align-items: flex-start;
  gap: ${({ theme }) => theme.space.xs};
  margin-bottom: ${({ theme }) => theme.space.xs};
  font-size: ${({ theme }) => theme.font.size.sm};

  &:last-child {
    margin-bottom: 0;
  }

  svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    margin-top: 2px;
    color: ${({ theme }) => theme.palette.text.secondary};
  }
`;

export const BookingInfoLabel = styled.span`
  color: ${({ theme }) => theme.palette.text.secondary};
  min-width: 100px;
  flex-shrink: 0;
`;

export const BookingInfoValue = styled.span`
  color: ${({ theme }) => theme.palette.text.primary};
  font-weight: ${({ theme }) => theme.font.weight.medium};
  flex: 1;
`;

export const BookingConfirmationCode = styled.div`
  display: inline-flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xs};
  padding: ${({ theme }) => theme.space.sm} ${({ theme }) => theme.space.md};
  background: ${({ theme }) => theme.palette.background.default};
  border: 2px dashed ${({ theme }) => theme.palette.primary};
  border-radius: ${({ theme }) => theme.radius.base}px;
  font-size: ${({ theme }) => theme.font.size.base};
  font-weight: ${({ theme }) => theme.font.weight.bold};
  color: ${({ theme }) => theme.palette.primary};
  font-family: monospace;
  letter-spacing: 1px;
  margin-top: ${({ theme }) => theme.space.xs};
`;

export const BookingError = styled.div`
  padding: ${({ theme }) => theme.space.sm} ${({ theme }) => theme.space.md};
  background: rgba(255, 77, 79, 0.1);
  border-left: 3px solid ${({ theme }) => theme.palette.error || '#ff4d4f'};
  border-radius: ${({ theme }) => theme.radius.sm}px;
  color: ${({ theme }) => theme.palette.error || '#ff4d4f'};
  font-size: ${({ theme }) => theme.font.size.sm};
  margin-top: ${({ theme }) => theme.space.sm};
  display: flex;
  gap: ${({ theme }) => theme.space.xs};

  svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    margin-top: 2px;
  }
`;

export const BookingTimestamp = styled.div`
  padding-top: ${({ theme }) => theme.space.sm};
  margin-top: ${({ theme }) => theme.space.sm};
  border-top: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: ${({ theme }) => theme.space.xs};
`;

export const CallCardsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.md};
  width: 100%;
  overflow: visible;
`;

export const CallCardsScroll = styled(ProviderCardsScroll)``;

export const CallCard = styled.div`
  background: ${({ theme }) => theme.palette.background.paper};
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  overflow: hidden;
  transition: all 0.2s;
  cursor: pointer;
  flex: 0 0 auto;
  width: 340px;
  min-width: 340px;
  scroll-snap-align: start;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 300px;
    min-width: 300px;
  }

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

export const CallCardHeader = styled.div<{ $status?: string }>`
  padding: ${({ theme }) => theme.space.md};
  background: ${({ $status, theme }) =>
    $status === 'active' || $status === 'connected'
      ? 'rgba(82, 196, 26, 0.1)'
      : $status === 'initiating'
        ? 'rgba(250, 173, 20, 0.1)'
        : $status === 'ringing'
          ? 'rgba(24, 144, 255, 0.1)'
          : $status === 'connecting'
            ? 'rgba(135, 108, 249, 0.1)'
            : $status === 'ended'
              ? `${theme.palette.primary}15`
              : $status === 'failed'
                ? 'rgba(255, 77, 79, 0.1)'
                : theme.palette.background.default};
  border-bottom: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.md};
`;

export const CallIconWrapper = styled.div<CallIconWrapperProps>`
  width: 48px;
  height: 48px;
  border-radius: ${({ theme }) => theme.radius.circle};
  background: ${({ $status, theme }) =>
    $status === 'active' || $status === 'connected'
      ? theme.palette.success || '#52c41a'
      : $status === 'initiating'
        ? theme.palette.warning || '#faad14'
        : $status === 'ringing'
          ? theme.palette.info || '#1890ff'
          : $status === 'connecting'
            ? '#876CF9'
            : $status === 'ended'
              ? theme.palette.primary
              : $status === 'failed'
                ? theme.palette.error || '#ff4d4f'
                : theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  svg {
    width: 24px;
    height: 24px;
  }

  ${({ $status }) =>
    ($status === 'ringing' || $status === 'connecting') &&
    `
    animation: pulse 1.5s ease-in-out infinite;
  `}

  ${({ $status }) =>
    $status === 'initiating' &&
    `
    animation: spin 2s linear infinite;
  `}

  @keyframes pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.05);
      opacity: 0.8;
    }
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

export const CallHeaderContent = styled.div`
  flex: 1;
  min-width: 0;
`;

export const CallHeaderTop = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: ${({ theme }) => theme.space.sm};
  margin-bottom: ${({ theme }) => theme.space.xss};
`;

export const CallTitle = styled.h3`
  margin: 0;
  font-size: ${({ theme }) => theme.font.size.lg};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  color: ${({ theme }) => theme.palette.text.primary};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

export const CallStatus = styled.span<{ $status?: string }>`
  display: inline-flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xss};
  padding: ${({ theme }) => theme.space.xss} ${({ theme }) => theme.space.sm};
  background: ${({ $status, theme }) =>
    $status === 'active' || $status === 'connected'
      ? theme.palette.success || '#52c41a'
      : $status === 'initiating'
        ? theme.palette.warning || '#faad14'
        : $status === 'ringing'
          ? theme.palette.info || '#1890ff'
          : $status === 'connecting'
            ? '#876CF9'
            : $status === 'ended'
              ? theme.palette.primary
              : $status === 'failed'
                ? theme.palette.error || '#ff4d4f'
                : theme.palette.background.default};
  color: ${({ theme }) => theme.palette.common.white};
  border-radius: ${({ theme }) => theme.radius.base}px;
  font-size: ${({ theme }) => theme.font.size.sm};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  text-transform: uppercase;
  flex-shrink: 0;
  opacity: ${({ $status }) => ($status === 'ended' ? 0.75 : 1)};

  ${({ $status }) =>
    ($status === 'ringing' || $status === 'connecting') &&
    `
    animation: blink 1s ease-in-out infinite;
  `}

  @keyframes blink {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }
`;

export const CallPhone = styled.div`
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xss};

  a {
    color: inherit;
    text-decoration: none;

    &:hover {
      color: ${({ theme }) => theme.palette.primary};
    }
  }
`;

export const CallCardBody = styled.div`
  padding: ${({ theme }) => theme.space.md};
`;

export const CallStats = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: ${({ theme }) => theme.space.md};
`;

export const CallStatItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.xss};
`;

export const CallStatLabel = styled.span`
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: ${({ theme }) => theme.font.weight.medium};
`;

export const CallStatValue = styled.span`
  font-size: ${({ theme }) => theme.font.size.lg};
  color: ${({ theme }) => theme.palette.text.primary};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  font-family: monospace;
`;

export const CallDuration = styled.div`
  display: inline-flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xs};
  padding: ${({ theme }) => theme.space.sm} ${({ theme }) => theme.space.md};
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.radius.base}px;
  font-size: ${({ theme }) => theme.font.size.base};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  color: ${({ theme }) => theme.palette.text.primary};
  margin-top: ${({ theme }) => theme.space.sm};

  svg {
    width: 16px;
    height: 16px;
    color: ${({ theme }) => theme.palette.text.secondary};
  }
`;

export const CallError = styled.div`
  padding: ${({ theme }) => theme.space.sm} ${({ theme }) => theme.space.md};
  background: rgba(255, 77, 79, 0.1);
  border-left: 3px solid ${({ theme }) => theme.palette.error || '#ff4d4f'};
  border-radius: ${({ theme }) => theme.radius.sm}px;
  color: ${({ theme }) => theme.palette.error || '#ff4d4f'};
  font-size: ${({ theme }) => theme.font.size.sm};
  margin-top: ${({ theme }) => theme.space.sm};
  display: flex;
  gap: ${({ theme }) => theme.space.xs};

  svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    margin-top: 2px;
  }
`;

export const EventCardsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.md};
  width: 100%;
  overflow: visible;
`;

export const EventCardsScroll = styled(ProviderCardsScroll)``;

export const EventCard = styled.div`
  background: ${({ theme }) => theme.palette.background.paper};
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  flex: 0 0 auto;
  width: 340px;
  min-width: 340px;
  scroll-snap-align: start;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.06),
    0 1px 2px rgba(0, 0, 0, 0.04);

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 300px;
    min-width: 300px;
  }

  &:hover {
    border-color: ${({ theme }) => theme.palette.primary}60;
    box-shadow:
      0 8px 24px rgba(0, 0, 0, 0.12),
      0 4px 8px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
  }

  &:active {
    transform: translateY(0);
  }
`;

export const EventCardBanner = styled.img`
  width: 100%;
  height: 160px;
  object-fit: cover;
  background: linear-gradient(
    135deg,
    ${({ theme }) => theme.palette.primary}15 0%,
    ${({ theme }) => theme.palette.primary}05 100%
  );
  transition: transform 0.3s ease;

  ${EventCard}:hover & {
    transform: scale(1.05);
  }
`;

export const EventCardContent = styled.div`
  padding: ${({ theme }) => theme.space.md} ${({ theme }) => theme.space.lg};
`;

export const EventCardTitle = styled.h3`
  margin: 0 0 ${({ theme }) => theme.space.xs};
  font-size: 16px;
  font-weight: ${({ theme }) => theme.font.weight.bold};
  color: ${({ theme }) => theme.palette.text.primary};
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  letter-spacing: -0.01em;
`;

export const EventCardDescription = styled.p`
  margin: 0 0 ${({ theme }) => theme.space.md};
  font-size: 13px;
  color: ${({ theme }) => theme.palette.text.secondary};
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

export const EventTags = styled.div`
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: ${({ theme }) => theme.space.md};
`;

export const EventTag = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: linear-gradient(
    135deg,
    ${({ theme }) => theme.palette.primary}12 0%,
    ${({ theme }) => theme.palette.primary}08 100%
  );
  border-radius: 12px;
  font-size: 11px;
  color: ${({ theme }) => theme.palette.primary};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  border: 1px solid ${({ theme }) => theme.palette.primary}20;
  transition: all 0.2s;

  &:hover {
    background: ${({ theme }) => theme.palette.primary}20;
    border-color: ${({ theme }) => theme.palette.primary}40;
  }
`;

export const EventDetails = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.xs};
  padding-top: ${({ theme }) => theme.space.xs};
  border-top: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
`;

export const EventDetailRow = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xss};
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};

  svg {
    width: 14px;
    height: 14px;
    flex-shrink: 0;
    color: ${({ theme }) => theme.palette.text.secondary};
  }

  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
`;

export const EventDate = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: linear-gradient(
    135deg,
    ${({ theme }) => theme.palette.primary}15 0%,
    ${({ theme }) => theme.palette.primary}08 100%
  );
  color: ${({ theme }) => theme.palette.primary};
  border-radius: 12px;
  font-weight: ${({ theme }) => theme.font.weight.bold};
  font-size: 12px;
  margin-top: ${({ theme }) => theme.space.xs};
  border: 1px solid ${({ theme }) => theme.palette.primary}20;

  svg {
    width: 16px;
    height: 16px;
  }
`;

export const EventQueryHeader = styled.div`
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  margin-bottom: ${({ theme }) => theme.space.md};
  font-weight: ${({ theme }) => theme.font.weight.medium};
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xs};

  &::before {
    content: '🔍';
    font-size: 14px;
  }
`;

export const PersonCardsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.md};
  width: 100%;
  overflow: visible;
`;

export const PersonCardsScroll = styled(ProviderCardsScroll)``;

export const PersonCard = styled.div`
  background: ${({ theme }) => theme.palette.background.paper};
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  overflow: hidden;
  transition: all 0.2s;
  cursor: pointer;
  flex: 0 0 auto;
  width: 320px;
  min-width: 320px;
  scroll-snap-align: start;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 280px;
    min-width: 280px;
  }

  &:hover {
    border-color: ${({ theme }) => theme.palette.primary};
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

export const PersonCardHeader = styled.div`
  padding: ${({ theme }) => theme.space.md};
  display: flex;
  gap: ${({ theme }) => theme.space.md};
  align-items: flex-start;
`;

export const PersonAvatar = styled.img`
  width: 80px;
  height: 80px;
  border-radius: ${({ theme }) => theme.radius.circle};
  object-fit: cover;
  flex-shrink: 0;
  background: ${({ theme }) => theme.palette.background.default};
  border: 2px solid ${({ theme }) => theme.border.color};
`;

export const PersonInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

export const PersonName = styled.h3`
  margin: 0 0 ${({ theme }) => theme.space.xss};
  font-size: ${({ theme }) => theme.font.size.lg};
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  color: ${({ theme }) => theme.palette.text.primary};
`;

export const PersonTitleCompany = styled.div`
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  margin-bottom: ${({ theme }) => theme.space.xs};
`;

export const PersonScore = styled.div`
  display: inline-flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xss};
  padding: ${({ theme }) => theme.space.xss} ${({ theme }) => theme.space.xs};
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.radius.sm}px;
  font-size: ${({ theme }) => theme.font.size.sm};
  font-weight: ${({ theme }) => theme.font.weight.medium};
  color: ${({ theme }) => theme.palette.text.primary};

  svg {
    width: 12px;
    height: 12px;
    color: ${({ theme }) => theme.palette.warning || '#faad14'};
  }
`;

export const PersonCardBody = styled.div`
  padding: 0 ${({ theme }) => theme.space.md} ${({ theme }) => theme.space.md};
`;

export const PersonDescription = styled.p`
  margin: 0 0 ${({ theme }) => theme.space.md};
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

export const PersonSocialLinks = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.space.sm};
  padding-top: ${({ theme }) => theme.space.sm};
  border-top: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
`;

export const PersonSocialLink = styled.a`
  display: inline-flex;
  align-items: center;
  gap: ${({ theme }) => theme.space.xs};
  padding: ${({ theme }) => theme.space.xs} ${({ theme }) => theme.space.sm};
  background: ${({ theme }) => theme.palette.background.default};
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  color: ${({ theme }) => theme.palette.text.primary};
  text-decoration: none;
  font-size: ${({ theme }) => theme.font.size.sm};
  font-weight: ${({ theme }) => theme.font.weight.medium};
  transition: all 0.2s;

  svg {
    width: 14px;
    height: 14px;
    color: ${({ theme }) => theme.palette.text.secondary};
  }

  &:hover {
    background: ${({ theme }) => theme.palette.primary};
    color: ${({ theme }) => theme.palette.common.white};
    border-color: ${({ theme }) => theme.palette.primary};

    svg {
      color: ${({ theme }) => theme.palette.common.white};
    }
  }
`;

export const PersonQueryHeader = styled.div`
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  margin-bottom: ${({ theme }) => theme.space.sm};
  font-style: italic;
`;

// Card Detail Modal Components
export const CardModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: ${({ theme }) => theme.space.lg};
  animation: fadeIn 0.2s ease;

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`;

export const CardModalContent = styled.div`
  background: ${({ theme }) => theme.palette.background.paper};
  border-radius: ${({ theme }) => theme.radius.base}px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;

  @keyframes slideUp {
    from {
      transform: translateY(20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.palette.primary}40;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
`;

export const CardModalHeader = styled.div`
  position: sticky;
  top: 0;
  background: ${({ theme }) => theme.palette.background.paper};
  padding: ${({ theme }) => theme.space.lg};
  border-bottom: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 1;
`;

export const CardModalTitle = styled.h2`
  margin: 0;
  font-size: ${({ theme }) => theme.font.size.lg};
  font-weight: ${({ theme }) => theme.font.weight.bold};
  color: ${({ theme }) => theme.palette.text.primary};
`;

export const CardModalClose = styled.button`
  background: none;
  border: none;
  padding: ${({ theme }) => theme.space.xs};
  cursor: pointer;
  color: ${({ theme }) => theme.palette.text.secondary};
  border-radius: ${({ theme }) => theme.radius.circle};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  svg {
    width: 24px;
    height: 24px;
  }

  &:hover {
    background: ${({ theme }) => theme.palette.background.default};
    color: ${({ theme }) => theme.palette.text.primary};
  }
`;

export const CardModalBody = styled.div`
  padding: ${({ theme }) => theme.space.lg};
`;
