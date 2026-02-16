'use client';
import React, { useState } from 'react';
import { StyledInputWrapper } from './index.styled';
import { AppInput } from '@unpod/components/antd';
import { Typography } from 'antd';
import { useIntl } from 'react-intl';

const { Title, Text } = Typography;

type PlatformInputProps = {
  title?: string;
  placeholder?: string;
  setBasicDetail: (detail: string) => void;
};

const PlatformInput: React.FC<PlatformInputProps> = ({
  title,
  placeholder,
  setBasicDetail,
}) => {
  const { formatMessage } = useIntl();
  const [loading, setLoading] = useState(false);
  const [url, setUrl] = useState('');

  const fetchExaContent = async (targetUrl: string) => {
    if (!targetUrl) {
      setBasicDetail('');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('https://api.exa.ai/contents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'efde05f2-61b1-4899-8329-31ba9e56946e', // Replace with your actual API key
        },
        body: JSON.stringify({ urls: [targetUrl], text: true }),
      });

      if (!response.ok) {
        console.error('Failed to fetch content');
        setBasicDetail('');
        return;
      }

      const data = await response.json();
      // Extract text content from the first result
      const content = data?.results?.[0]?.text || '';
      setBasicDetail(content);
    } catch (error) {
      console.error('Error fetching content:', error);
      setBasicDetail('');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      fetchExaContent(url);
    }
  };

  return (
    <StyledInputWrapper>
      <Title level={4}>
        {formatMessage({ id: 'onboarding.enterUrlTitle' }, { title })}
      </Title>
      <AppInput
        placeholder={placeholder || ''}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        suffix={
          loading ? (
            <span>{formatMessage({ id: 'common.loading' })}</span>
          ) : null
        }
      />

      <Text strong style={{ fontSize: 12, marginTop: 4 }}>
        {formatMessage({ id: 'onboarding.analyzeProfileDesc' })}
      </Text>
    </StyledInputWrapper>
  );
};

export default PlatformInput;
