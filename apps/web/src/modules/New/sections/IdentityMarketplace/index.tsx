'use client';
import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import {
  StyledAiTag,
  StyledCard,
  StyledCardIcon,
  StyledDescription,
  StyledGrid,
  StyledIconWrapper,
  StyledSubTitle,
  Styledtext,
  StyledTitle,
} from './index.styled';
import { FaHeadphones } from 'react-icons/fa6';
import { IoMdMail } from 'react-icons/io';
import { HiOutlineUsers } from 'react-icons/hi';
import { Card } from 'antd';
import { useIntl } from 'react-intl';

const { Meta } = Card;

const usersData = [
  {
    nameId: 'identityMarketplace.user1.name',
    aiNameId: 'identityMarketplace.user1.aiName',
    descriptionId: 'identityMarketplace.user1.description',
    icon: <FaHeadphones />,
  },
  {
    nameId: 'identityMarketplace.user2.name',
    aiNameId: 'identityMarketplace.user2.aiName',
    descriptionId: 'identityMarketplace.user2.description',
    icon: <IoMdMail />,
  },
  {
    nameId: 'identityMarketplace.user3.name',
    aiNameId: 'identityMarketplace.user3.aiName',
    descriptionId: 'identityMarketplace.user3.description',
    icon: <HiOutlineUsers />,
  },
];

const IdentityMarketplace = () => {
  const { formatMessage } = useIntl();

  return (
    <AppPageSection
      style={{
        background:
          'radial-gradient(ellipse 60% 40% at 80% 30%, #e5d6ff 0%, #f8fafd 60%, #f6e5fa 100%)',
      }}
    >
      <StyledTitle>
        {formatMessage({ id: 'identityMarketplace.title' })}
      </StyledTitle>
      <StyledSubTitle>
        {formatMessage({ id: 'identityMarketplace.subTitle' })}
      </StyledSubTitle>
      <StyledDescription>
        {formatMessage({ id: 'identityMarketplace.description' })}
      </StyledDescription>

      <StyledGrid>
        {usersData.map((user, index) => (
          <StyledCard key={index}>
            <StyledCardIcon>
              {formatMessage({ id: user.nameId }).charAt(0)}
            </StyledCardIcon>
            <Meta
              title={
                <StyledIconWrapper>
                  {user.icon}
                  <Styledtext>{formatMessage({ id: user.nameId })}</Styledtext>
                </StyledIconWrapper>
              }
            />
            <StyledIconWrapper>
              <StyledAiTag>{formatMessage({ id: user.aiNameId })}</StyledAiTag>
            </StyledIconWrapper>
            <Meta description={formatMessage({ id: user.descriptionId })} />
          </StyledCard>
        ))}
      </StyledGrid>
    </AppPageSection>
  );
};

export default IdentityMarketplace;
