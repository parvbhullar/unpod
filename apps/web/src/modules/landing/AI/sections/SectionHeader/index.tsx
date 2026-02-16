'use client';
import React from 'react';
import { Button } from 'antd';
import AppImage from '@unpod/components/next/AppImage';
import AppLink from '@unpod/components/next/AppLink';
import {
  StyledActionsWrapper,
  StyledGitHubButton,
  StyledPurpleText,
  StyledRoot,
  StyledSubTitle,
  StyledTagline,
  StyledTaglineWrapper,
  StyledTitle,
  StyledWordPressTitle,
} from './index.styled';
import { MdArrowOutward, MdOutlineWorkspaces } from 'react-icons/md';
import { RiGithubFill, RiStarFill } from 'react-icons/ri';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@unpod/providers';
import { StyledButton } from '@/core/AppLayout/FrontendLayout/LayoutHeader/index.styled';
import { isEmptyObject } from '@unpod/helpers/GlobalHelper';
import { useMediaQuery } from 'react-responsive';
import { TabWidthQuery } from '@unpod/constants';
import { useIntl } from 'react-intl';
import AnimatedSphere from '@unpod/livekit/AppVoiceAgent/AnimatedSphere';

const SectionHeader = () => {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthContext();
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const { formatMessage } = useIntl();

  const handleContactUsClick = () => {
    router.push('/contact-us/');
  };

  const joinOrCreateHub = async () => {
    if (isEmptyObject(user?.organization as Record<string, unknown>)) {
      // await router.push('/create-org');
      if (user?.is_private_domain) {
        await router.push('/creating-identity/');
      } else {
        await router.push('/business-identity/');
      }
    } else {
      await router.push('/join-org');
    }
  };
  const goToMyHub = async () => {
    await router.push(`/spaces/${user?.active_space?.slug}/call/`);
  };

  return (
    <StyledRoot>
      <StyledTaglineWrapper className="logo">
        <StyledTagline>
          <span className="text">
            {formatMessage({ id: 'aiSectionHeader.tagline' })}
          </span>
          <span
            style={{
              color: '#796CFF',
              justifyContent: 'center',
              display: 'flex',
            }}
          >
            <AppLink href="https://unpod.dev/" style={{ display: 'flex' }}>
              <AppImage
                src="/images/unpod/logo.svg"
                alt="unpod logo"
                height={17}
                width={60}
              />
              <span> .dev</span>
            </AppLink>
          </span>
        </StyledTagline>
      </StyledTaglineWrapper>

      <div style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
        <AnimatedSphere
          size={250}
          breakpoints={{
            mobile: 200,
            tablet: 230,
            desktop: 250,
          }}
        />
      </div>

      <StyledTitle>
        <StyledWordPressTitle>WordPress</StyledWordPressTitle> for{' '}
        <StyledPurpleText>Communication</StyledPurpleText>
      </StyledTitle>

      <StyledSubTitle level={2}>
        An <strong>open source platform</strong> for building Voice Agents,
        customise the agent personality, functionality, themes and data model in
        minutes not weeks.
      </StyledSubTitle>

      {isAuthenticated ? (
        <StyledActionsWrapper>
          <StyledGitHubButton
            href="https://github.com/parvbhullar/unpod"
            target="_blank"
            rel="noopener noreferrer"
          >
            <RiGithubFill fontSize={isTabletOrMobile ? 20 : 22} />
            {!isTabletOrMobile && 'Start Building'}
            <RiStarFill
              className="star-icon"
              fontSize={isTabletOrMobile ? 14 : 16}
            />
          </StyledGitHubButton>
          {user?.current_step === 'join_organization' ||
          user?.current_step === 'organization' ? (
            <StyledButton
              type="primary"
              shape="round"
              size="middle"
              onClick={joinOrCreateHub}
            >
              {isTabletOrMobile ? (
                <MdOutlineWorkspaces fontSize={18} />
              ) : isEmptyObject(
                  user?.organization as Record<string, unknown>,
                ) ? (
                formatMessage({ id: 'aiSectionHeader.createOrg' })
              ) : (
                formatMessage({ id: 'aiSectionHeader.joinOrg' })
              )}
            </StyledButton>
          ) : (
            <StyledButton
              type="primary"
              shape="round"
              size="middle"
              iconPosition="end"
              icon={<MdArrowOutward fontSize={isTabletOrMobile ? 18 : 24} />}
              onClick={goToMyHub}
            >
              {formatMessage({ id: 'aiSectionHeader.mySpace' })}
            </StyledButton>
          )}
        </StyledActionsWrapper>
      ) : (
        <StyledActionsWrapper>
          <StyledGitHubButton
            href="https://github.com/parvbhullar/unpod"
            target="_blank"
            rel="noopener noreferrer"
          >
            <RiGithubFill fontSize={isTabletOrMobile ? 20 : 22} />
            {!isTabletOrMobile && 'Start Building'}
            <RiStarFill
              className="star-icon"
              fontSize={isTabletOrMobile ? 14 : 16}
            />
          </StyledGitHubButton>
          <Button
            type="primary"
            shape="round"
            iconPosition="end"
            size="middle"
            icon={<MdArrowOutward fontSize={isTabletOrMobile ? 18 : 24} />}
            onClick={handleContactUsClick}
          >
            {formatMessage({ id: 'aiSectionHeader.build' })}
          </Button>
        </StyledActionsWrapper>
      )}

      {/*<CarouselContainer>
        <Carousel ref={carouselRef} {...leadCarouselSettings}>
          {leadCardsData.map((singleCardData) => (
            <div key={singleCardData.id}>
              <StyledCard
                style={{ backgroundImage: `url(${singleCardData.image})` }}
              >
                <StyledBadgesContainer>
                  <StyledBadge title="Language">
                    {singleCardData.language}
                  </StyledBadge>
                  <StyledBadge title="Accent">
                    {singleCardData.accent}
                  </StyledBadge>
                </StyledBadgesContainer>

                <StyledCardContent>
                  <StyledCardTitle>{singleCardData.title}</StyledCardTitle>
                  <StyledCardSubtitle>
                    {singleCardData.subtitle}
                  </StyledCardSubtitle>

                  <AgentConnectionProvider>
                    <Agent singleCardData={singleCardData} />
                  </AgentConnectionProvider>
                </StyledCardContent>
              </StyledCard>
            </div>
          ))}
        </Carousel>
        <NavButton
          className="prev-button"
          onClick={prevSlide}
          style={{ left: 0 }}
        >
          <LeftOutlined />
        </NavButton>
        <NavButton
          className="next-button"
          onClick={nextSlide}
          style={{ right: 0 }}
        >
          <RightOutlined />
        </NavButton>
      </CarouselContainer>*/}
    </StyledRoot>
  );
};

export default SectionHeader;
