import React from 'react';
import { StarOutlined } from '@ant-design/icons';
import {
  StyledCard,
  StyledDescription,
  StyledHeaderRow,
  StyledLogoAndTitle,
  StyledLogoWrapper,
  StyledNameSubtitleBlock,
  StyledPopularBadge,
  StyledReadyDot,
  StyledStatusLabel,
  StyledStatusRow,
  StyledStatusText,
  StyledSubtitle,
  StyledTitle,
} from './index.styled';
import { Image } from 'antd';
import { useIntl } from 'react-intl';

type PlatformItemData = {
  logo: string;
  name: string;
  subtitle: string;
  popular: boolean;
  description: string;
  status: string;
  statusColor?: string;
};

type PlatformItemProps = {
  item: PlatformItemData;
};

const PlatformItem: React.FC<PlatformItemProps> = ({ item }) => {
  const { formatMessage } = useIntl();
  const highlight = item.popular ? '#cfe3fd' : 'transparent';
  return (
    <StyledCard $highlight={highlight}>
      <StyledHeaderRow>
        <StyledLogoAndTitle>
          <StyledLogoWrapper>
            <Image src={item.logo} alt={item.name} />
          </StyledLogoWrapper>
          <StyledNameSubtitleBlock>
            <StyledTitle>{formatMessage({ id: item.name })}</StyledTitle>
            <StyledSubtitle>
              {formatMessage({ id: item.subtitle })}
            </StyledSubtitle>
          </StyledNameSubtitleBlock>
        </StyledLogoAndTitle>
        {item.popular && (
          <StyledPopularBadge>
            <StarOutlined
              style={{ fontSize: 12, marginRight: 6, color: '#FFFFFF' }}
            />
            {formatMessage({ id: 'sipPlatforms.popular' })}
          </StyledPopularBadge>
        )}
      </StyledHeaderRow>
      <StyledDescription>
        {formatMessage({ id: item.description })}
      </StyledDescription>
      {/*  <StyledFeaturesList>
        {item.features.map((feature) => (
          <StyledFeature key={feature}>
            <CheckCircleOutlined />
            {feature}
          </StyledFeature>
        ))}
      </StyledFeaturesList>*/}
      <StyledStatusRow>
        <StyledStatusLabel>
          {formatMessage({ id: 'sipPlatforms.integrationStatus' })}
        </StyledStatusLabel>
        <span>
          <StyledReadyDot $bgColor={item.statusColor} />
          <StyledStatusText $color={item.statusColor}>
            {formatMessage({ id: item.status })}
          </StyledStatusText>
        </span>
      </StyledStatusRow>
    </StyledCard>
  );
};

export default PlatformItem;
