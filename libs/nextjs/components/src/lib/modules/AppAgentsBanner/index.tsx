import type { HTMLAttributes } from 'react';

import { Button, Divider, Image, Typography } from 'antd';
import { BsStars } from 'react-icons/bs';
import { useRouter } from 'next/navigation';
import { getImageUrl } from '@unpod/helpers/UrlHelper';
import {
  StyledBannerContainer,
  StyledImageWrapper,
  StyledTextWrapper,
} from './index.styled';
import { useAuthContext } from '@unpod/providers';
import { useIntl } from 'react-intl';

const { Title } = Typography;

type AppAgentsBannerProps = HTMLAttributes<HTMLDivElement> & {
  showDivider?: boolean;};

const AppAgentsBanner = ({
  showDivider,
  ...restProps
}: AppAgentsBannerProps) => {
  const router = useRouter();
  const { isAuthenticated } = useAuthContext();
  const { formatMessage } = useIntl();

  const onCreateAiClick = () => {
    router.push('/ai-studio/new');
  };

  return (
    <StyledBannerContainer {...restProps}>
      <StyledImageWrapper>
        <Image
          src={getImageUrl('ai-agents-banner.png')}
          alt="AI Studio"
          className="banner-img"
        />
      </StyledImageWrapper>

      <StyledTextWrapper>
        <Title level={2}>Create an AI</Title>

        <Title level={5} type="secondary">
          {formatMessage({ id: 'appAgentsBanner.description' })}
        </Title>
      </StyledTextWrapper>

      {process.env.isDevMode === 'yes' && isAuthenticated ? (
        <Button
          type="primary"
          shape="round"
          icon={<BsStars fontSize={24} />}
          onClick={onCreateAiClick}
        >
          {formatMessage({ id: 'agent.createAnAI' })}
        </Button>
      ) : null}

      {showDivider && <Divider />}
    </StyledBannerContainer>
  );
};

export default AppAgentsBanner;
