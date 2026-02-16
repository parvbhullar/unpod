'use client';
import React, { useEffect, useState } from 'react';
import { Button, Tag, Typography } from 'antd';
import {
  AppleOutlined,
  ArrowDownOutlined,
  HddOutlined,
  LinuxOutlined,
  ThunderboltOutlined,
  WindowsOutlined,
} from '@ant-design/icons';
import AppPageSection from '@unpod/components/common/AppPageSection';
import {
  StyledDownloadCard,
  StyledDownloadCards,
  StyledHeroSection,
  StyledRequirementCard,
  StyledRequirementsGrid,
  StyledRequirementsSection,
  StyledRequirementsTitle,
  StyledRoot,
} from './index.styled';
import { useIntl } from 'react-intl';

const { Title, Paragraph } = Typography;

const detectOS = () => {
  if (typeof window === 'undefined') return null;

  const userAgent = window.navigator.userAgent.toLowerCase();
  const platform = window.navigator.platform?.toLowerCase() || '';

  if (
    platform.includes('mac') ||
    userAgent.includes('mac') ||
    userAgent.includes('darwin')
  ) {
    return 'macOS';
  }
  if (platform.includes('win') || userAgent.includes('win')) {
    return 'Windows';
  }
  if (platform.includes('linux') || userAgent.includes('linux')) {
    return 'Linux';
  }
  return null;
};

const sectionStyle = {
  background:
    'linear-gradient(248.95deg, #F2EEFF 3.95%, #FFEFFD 38.71%, #F2EEFF 70.73%, #FFEFFD 95.44%)',
  minHeight: 'calc(100vh - 200px)',
};

const DOWNLOAD_PLATFORMS = [
  {
    name: 'macOS',
    icon: <AppleOutlined />,
    version: 'Version 1.0.0',
    downloadUrl: '#',
    architectures: [
      { label: 'Apple Silicon', url: '#' },
      { label: 'Intel', url: '#' },
    ],
    buttonText: 'download.mac',
  },
  {
    name: 'Windows',
    icon: <WindowsOutlined />,
    version: 'Version 1.0.0',
    downloadUrl: '#',
    architectures: [
      { label: '64-bit', url: '#' },
      { label: '32-bit', url: '#' },
    ],
    buttonText: 'download.windows',
  },
  {
    name: 'Linux',
    icon: <LinuxOutlined />,
    version: 'Version 1.0.0',
    downloadUrl: '#',
    architectures: [
      { label: '.deb', url: '#' },
      { label: '.rpm', url: '#' },
      { label: '.AppImage', url: '#' },
    ],
    buttonText: 'download.linux',
  },
];

const SYSTEM_REQUIREMENTS = [
  {
    title: 'macOS',
    description: 'download.macos',
    icon: <AppleOutlined />,
  },
  {
    title: 'Windows',
    description: 'download.windowsReq',
    icon: <WindowsOutlined />,
  },
  {
    title: 'Linux',
    description: 'download.linuxReq',
    icon: <LinuxOutlined />,
  },
  {
    title: 'download.storageTitle',
    description: 'download.storage',
    icon: <HddOutlined />,
  },
  {
    title: 'download.memoryTitle',
    description: 'download.memory',
    icon: <ThunderboltOutlined />,
  },
];

const Download = () => {
  const [currentOS, setCurrentOS] = useState<
    'macOS' | 'Windows' | 'Linux' | null
  >(null);
  const { formatMessage } = useIntl();

  useEffect(() => {
    setCurrentOS(detectOS());
  }, []);

  return (
    <AppPageSection style={sectionStyle}>
      <StyledRoot>
        <StyledHeroSection>
          <Title className="hero-title">
            <span className="text-active">
              {formatMessage({ id: 'common.download' })}
            </span>
          </Title>
          <Paragraph className="hero-description">
            {formatMessage({ id: 'download.description' })}
          </Paragraph>
        </StyledHeroSection>

        <StyledDownloadCards>
          {DOWNLOAD_PLATFORMS.map((platform) => {
            const isCurrentOS = currentOS === platform.name;
            return (
              <StyledDownloadCard
                key={platform.name}
                $isCurrentOS={isCurrentOS}
              >
                {isCurrentOS && (
                  <Tag color="purple" className="recommended-tag">
                    {formatMessage({ id: 'download.recommended' })}
                  </Tag>
                )}
                <div className="platform-icon">{platform.icon}</div>
                <div className="platform-name">{platform.name}</div>
                <div className="platform-version">{platform.version}</div>
                <Button
                  type="primary"
                  size="large"
                  icon={<ArrowDownOutlined />}
                  className="download-btn"
                  href={platform.downloadUrl}
                >
                  {formatMessage({ id: platform.buttonText })}
                </Button>
                {platform.architectures && (
                  <div className="architecture-links">
                    {platform.architectures.map((arch, index) => (
                      <a key={arch.label} href={arch.url}>
                        {arch.label}
                        {index < platform.architectures.length - 1 && ''}
                      </a>
                    ))}
                  </div>
                )}
              </StyledDownloadCard>
            );
          })}
        </StyledDownloadCards>

        <StyledRequirementsSection>
          <StyledRequirementsTitle>
            {formatMessage({ id: 'download.system' })}{' '}
            <span>{formatMessage({ id: 'download.requirements' })}</span>
          </StyledRequirementsTitle>
          <StyledRequirementsGrid>
            {SYSTEM_REQUIREMENTS.map((req) => (
              <StyledRequirementCard key={req.title}>
                <div className="requirement-icon">{req.icon}</div>
                <div className="requirement-content">
                  <h4>{formatMessage({ id: req.title })}</h4>
                  <p>{formatMessage({ id: req.description })}</p>
                </div>
              </StyledRequirementCard>
            ))}
          </StyledRequirementsGrid>
        </StyledRequirementsSection>
      </StyledRoot>
    </AppPageSection>
  );
};

export default Download;
