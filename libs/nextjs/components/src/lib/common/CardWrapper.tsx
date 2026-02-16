import React, { ReactNode, useState } from 'react';
import { Button, Card, Flex, Space } from 'antd';
import { DownOutlined, UpOutlined } from '@ant-design/icons';
import styled from 'styled-components';
import { useIntl } from 'react-intl';

const AnimatedContent = styled.div<{ $isVisible: boolean }>`
  max-height: ${(props) => (props.$isVisible ? '5000px' : '0')};
  opacity: ${(props) => (props.$isVisible ? '1' : '0')};
  overflow: hidden;
  transition:
    max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
`;

type CardWrapperProps = {
  icon?: ReactNode;
  title?: ReactNode;
  description?: ReactNode;
  extra?: ReactNode;
  children?: ReactNode;
  expandable?: boolean;
  collapsedContent?: ReactNode;
  defaultExpanded?: boolean;};

const CardWrapper: React.FC<CardWrapperProps> = ({
  icon,
  title,
  description,
  extra,
  children,
  expandable = false,
  collapsedContent,
  defaultExpanded = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const { formatMessage } = useIntl();

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const extraContent = expandable ? (
    <Flex gap={8} align="center">
      <Button
        type="text"
        size="small"
        color="primary"
        icon={isExpanded ? <UpOutlined /> : <DownOutlined />}
        iconPlacement="end"
        onClick={toggleExpand}
      >
        {isExpanded
          ? formatMessage({ id: 'identityStudio.hideDetails' })
          : formatMessage({ id: 'identityStudio.showDetails' })}
      </Button>
    </Flex>
  ) : null;

  return (
    <Card
      size="small"
      extra={extra}
      title={
        <Flex align="center" flex="start">
          {icon}{' '}
          <span
            style={{
              marginLeft: 8,
              display: 'flex',
              flexDirection: 'column',
              marginTop: 0,
              marginBottom: 5,
            }}
          >
            {title}
            <span
              style={{
                fontWeight: 400,
                fontSize: 13,
                color: 'rgba(0,0,0,0.45)',
                marginTop: -4,
              }}
            >
              {description}
            </span>
          </span>
        </Flex>
      }
      style={{ borderRadius: 8, marginBottom: 24 }}
    >
      <Space
        orientation="vertical"
        size="middle"
        style={{ width: '100%', paddingLeft: 8, paddingRight: 8 }}
      >
        {children}
        {extraContent}

        {collapsedContent ? (
          <AnimatedContent $isVisible={isExpanded}>
            {collapsedContent}
          </AnimatedContent>
        ) : null}
      </Space>
    </Card>
  );
};

export default CardWrapper;
