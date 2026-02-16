'use client';

import { useEffect, useState } from 'react';
import { Button, Card, message, Space, Typography } from 'antd';
import {
  BugOutlined,
  CopyOutlined,
  CustomerServiceOutlined,
  HomeOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import styled from 'styled-components';
import UnpodLogoAnimation from '@unpod/components/common/UnpodLogoAnimation';
import { useIntl } from 'react-intl';
import type { ErrorBoundaryProps } from '@/types/common';

const { Title, Paragraph, Text } = Typography;

const ErrorContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
`;

const ErrorCard = styled(Card)`
  max-width: 600px;
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(121, 108, 255, 0.1);
  border: none;
  overflow: hidden;

  .ant-card-body {
    padding: 48px 40px;
    text-align: center;
  }

  @media (max-width: 576px) {
    .ant-card-body {
      padding: 32px 24px;
    }
  }
`;

const LogoWrapper = styled.div`
  margin-bottom: 32px;
  display: flex;
  justify-content: center;
`;

const ErrorTitle = styled(Title)`
  &.ant-typography {
    font-size: 32px;
    font-weight: 700;
    color: #3a3a3a;
    margin-bottom: 16px;

    @media (max-width: 576px) {
      font-size: 24px;
    }
  }
`;

const ErrorDescription = styled(Paragraph)`
  &.ant-typography {
    font-size: 16px;
    color: #898989;
    margin-bottom: 32px;
    line-height: 1.6;
  }
`;

const ActionButtons = styled(Space)`
  width: 100%;
  justify-content: center;
  margin-bottom: 24px;

  .ant-btn {
    border-radius: 8px;
    height: 44px;
    padding: 0 24px;
    font-weight: 500;
    font-size: 15px;

    &.ant-btn-primary {
      background: #796cff;
      border-color: #796cff;

      &:hover {
        background: #9d93ff;
        border-color: #9d93ff;
      }
    }
  }

  @media (max-width: 576px) {
    flex-direction: column;

    .ant-btn {
      width: 100%;
    }
  }
`;

const SuggestionsBox = styled.div`
  background: #f4f0ff;
  border-radius: 12px;
  padding: 20px;
  margin-top: 32px;
  text-align: left;
`;

const SuggestionTitle = styled(Text)`
  &.ant-typography {
    font-weight: 600;
    color: #796cff;
    display: block;
    margin-bottom: 12px;
    font-size: 14px;
  }
`;

const SuggestionList = styled.ul`
  margin: 0;
  padding-left: 20px;
  color: #565656;
  font-size: 14px;

  li {
    margin-bottom: 8px;
    line-height: 1.5;

    &:last-child {
      margin-bottom: 0;
    }
  }
`;

const ErrorCode = styled.div`
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e8e8e8;

  .error-details {
    background: #f7f7f7;
    border-radius: 8px;
    padding: 12px 16px;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 12px;
    color: #cf2a27;
    text-align: left;
    word-break: break-word;
    max-height: 100px;
    overflow-y: auto;
    cursor: pointer;
    transition: background 0.3s;

    &:hover {
      background: #efefef;
    }
  }
`;

const SupportLink = styled.div`
  margin-top: 20px;

  .ant-btn-text {
    color: #796cff;

    &:hover {
      color: #9d93ff;
    }
  }
`;

export default function Error({ error, reset }: ErrorBoundaryProps) {
  const { formatMessage } = useIntl();
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    // Log error to error reporting service
    console.error('Application error:', error);
    setErrorMessage(error?.message || error?.toString() || 'Unknown error');
  }, [error]);

  const copyErrorDetails = () => {
    const errorDetails = `
Error: ${errorMessage}
Stack: ${error?.stack || 'No stack trace available'}
Time: ${new Date().toISOString()}
URL: ${window.location.href}
    `.trim();

    navigator.clipboard.writeText(errorDetails);
    message.success('Error details copied to clipboard');
  };

  const handleGoHome = () => {
    window.location.href = '/';
  };

  const handleContactSupport = () => {
    // You can customize this to open a support modal or redirect to support page
    window.location.href = '/contact';
  };

  return (
    <ErrorContainer>
      <ErrorCard>
        <LogoWrapper>
          <UnpodLogoAnimation size={100} showOrbits={false} showGlow={true} />
        </LogoWrapper>

        <ErrorTitle level={2}>
          {formatMessage({ id: 'error.somethingWentWrong' }) ||
            'Something went wrong!'}
        </ErrorTitle>

        <ErrorDescription>
          {formatMessage({ id: 'error.unexpectedError' }) ||
            'We apologize for the inconvenience. An unexpected error has occurred.'}
        </ErrorDescription>

        <ActionButtons size="middle">
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={() => reset()}
          >
            {formatMessage({ id: 'common.tryAgain' }) || 'Try Again'}
          </Button>
          <Button icon={<HomeOutlined />} onClick={handleGoHome}>
            {formatMessage({ id: 'common.goHome' }) || 'Go Home'}
          </Button>
        </ActionButtons>

        <SuggestionsBox>
          <SuggestionTitle>
            {formatMessage({ id: 'error.whatYouCanDo' }) || 'What you can do:'}
          </SuggestionTitle>
          <SuggestionList>
            <li>
              {formatMessage({ id: 'error.suggestion1' }) ||
                'Refresh the page and try again'}
            </li>
            <li>
              {formatMessage({ id: 'error.suggestion2' }) ||
                'Clear your browser cache and cookies'}
            </li>
            <li>
              {formatMessage({ id: 'error.suggestion3' }) ||
                'Check your internet connection'}
            </li>
            <li>
              {formatMessage({ id: 'error.suggestion4' }) ||
                'Try accessing the page in a different browser'}
            </li>
          </SuggestionList>
        </SuggestionsBox>

        {errorMessage && (
          <ErrorCode>
            <div
              className="error-details"
              onClick={copyErrorDetails}
              title="Click to copy error details"
            >
              <BugOutlined /> {errorMessage}
            </div>
            <SupportLink>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={copyErrorDetails}
              >
                {formatMessage({ id: 'error.copyDetails' }) ||
                  'Copy Error Details'}
              </Button>
              <Button
                type="text"
                size="small"
                icon={<CustomerServiceOutlined />}
                onClick={handleContactSupport}
                style={{ marginLeft: 8 }}
              >
                {formatMessage({ id: 'common.contactSupport' }) ||
                  'Contact Support'}
              </Button>
            </SupportLink>
          </ErrorCode>
        )}
      </ErrorCard>
    </ErrorContainer>
  );
}
