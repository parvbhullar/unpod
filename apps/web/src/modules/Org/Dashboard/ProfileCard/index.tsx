import React from 'react';
import { Typography } from 'antd';
import clsx from 'clsx';
import { MdArrowForwardIos } from 'react-icons/md';
import {
  StyledActionWrapper,
  StyledButton,
  StyledIconWrapper,
  StyledMainContent,
  StyledMainInfo,
  StyledRoot,
} from './index.styled';
import AppLink from '@unpod/components/next/AppLink';
import { useIntl } from 'react-intl';

const { Title, Paragraph } = Typography;

type ProfileCardData = {
  name: string;
  description: string;
  url: string;
  icon?: React.ReactNode;
};

type ProfileCardProps = {
  profile: ProfileCardData;
};

const ProfileCard: React.FC<ProfileCardProps> = ({ profile }) => {
  const { formatMessage } = useIntl();
  return (
    <StyledRoot className={clsx('profile')}>
      <StyledMainContent>
        <StyledIconWrapper>
          {/*<AppImage src={profile.icon} alt={profile.name} width={36} height={36} />*/}
          {profile.icon}
        </StyledIconWrapper>

        <StyledMainInfo>
          <Title level={5}>{formatMessage({ id: profile.name })}</Title>
          <Paragraph type="secondary">
            {formatMessage({ id: profile.description })}
          </Paragraph>
        </StyledMainInfo>
      </StyledMainContent>

      <StyledActionWrapper>
        <AppLink href={profile.url}>
          <StyledButton
            // type="text"
            shape="circle"
            icon={<MdArrowForwardIos fontSize={21} />}
            // ghost
          />
        </AppLink>
      </StyledActionWrapper>
    </StyledRoot>
  );
};

export default ProfileCard;
