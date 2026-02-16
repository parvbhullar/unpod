'use client';
import React from 'react';
import { useSearchParams } from 'next/navigation';
import {
  StyledRoot,
  StyledDotPattern,
  StyledRadialGlow,
  StyledTopLeftDiamonds,
  StyledBottomRightBlocks,
  StyledBlock,
  StyledChevronsLeft,
  StyledChevronsRight,
  StyledChevron,
  StyledScopeCircle,
  StyledLogo,
  StyledContentArea,
  StyledAvatarSection,
  StyledVideoAvatar,
  StyledVoiceSection,
  StyledTextSection,
  StyledHeadingPrimary,
  StyledHeadingSecondary,
  StyledBadgesRow,
  StyledBadge,
  StyledFooterBar,
} from './index.styled';
import AppVoice from '@unpod/livekit/AppVoiceAgent/voice';
import { useAuthContext } from '@unpod/providers';
import { MdLanguage, MdLocalPhone, MdMailOutline } from 'react-icons/md';

const AVATAR_VIDEO_URL =
  'https://jvibf5nnq6o5aohj.public.blob.vercel-storage.com/landingPageAssets/jess_intro_compressed.webm';

const UpAgent = () => {
  const searchParams = useSearchParams();
  const agentId = searchParams.get('id') || undefined;
  const { user } = useAuthContext() || {};

  const firstName = user?.first_name || 'Parvinder';
  const lastName = user?.last_name || 'Singh';

  return (
    <StyledRoot>
      {/* Background layers */}
      <StyledDotPattern />
      <StyledRadialGlow />

      {/* Corner decorations */}
      <StyledTopLeftDiamonds />
      <StyledBottomRightBlocks>
        {/* 3D isometric stair blocks */}
        <StyledBlock $w={200} $h={120} $bottom={-20} $right={-30} $bg="#1e293b" $skewX={-10} />
        <StyledBlock $w={160} $h={100} $bottom={0} $right={10} $bg="#2d3a4d" $skewX={-10} />
        <StyledBlock $w={120} $h={80} $bottom={20} $right={50} $bg="#3b4a5e" $skewX={-10} />
        <StyledBlock $w={80} $h={60} $bottom={40} $right={80} $bg="#4a5a6e" $skewX={-10} />
      </StyledBottomRightBlocks>

      {/* Chevron arrows */}
      <StyledChevronsLeft>
        <StyledChevron $direction="right" />
        <StyledChevron $direction="right" />
        <StyledChevron $direction="right" />
        <StyledChevron $direction="right" />
      </StyledChevronsLeft>
      <StyledChevronsRight>
        <StyledChevron $direction="left" />
        <StyledChevron $direction="left" />
        <StyledChevron $direction="left" />
        <StyledChevron $direction="left" />
      </StyledChevronsRight>

      {/* Scope circles */}
      <StyledScopeCircle $top="35%" $left="4%" $size={65} />
      <StyledScopeCircle $bottom="30%" $right="6%" $size={55} />

      {/* Unpod logo top‑right */}
      <StyledLogo>
        <img
          src="/images/unpod/logo.svg"
          alt="unpod logo"
        />
      </StyledLogo>

      {/* Avatar – absolutely positioned on the left */}
      <StyledAvatarSection>
        <StyledVideoAvatar
          src={AVATAR_VIDEO_URL}
          autoPlay
          loop
          muted
          playsInline
        />
        <StyledVoiceSection>
          <AppVoice
            agentId={agentId}
            spaceToken={
              user?.active_space?.token || 'FXBN30TOT8K9GUZT7IYV4ZWR'
            }
            agentName={'Unpod'}
            name={`${firstName} ${lastName}`.trim()}
            email={user?.email || 'parvinder@recalll.co'}
            conatctName={`${firstName} ${lastName}`.trim()}
          />
        </StyledVoiceSection>
      </StyledAvatarSection>

      {/* Main content – centred on full page */}
      <StyledContentArea>
        <StyledTextSection>
          <StyledHeadingPrimary>Open-Source</StyledHeadingPrimary>
          <StyledHeadingSecondary>
            Voice AI Platform
            <br />
            &amp;
            <br />
            SIP Infrastructure
          </StyledHeadingSecondary>
          <StyledBadgesRow>
            <StyledBadge>Voice Agents in Mins</StyledBadge>
            <StyledBadge>&lt;5 Min Set Up</StyledBadge>
            <StyledBadge>Ultra Low Latency</StyledBadge>
          </StyledBadgesRow>
        </StyledTextSection>
      </StyledContentArea>

      {/* Footer contact bar */}
      <StyledFooterBar>
        <a
          href="https://www.unpod.ai"
          target="_blank"
          rel="noopener noreferrer"
        >
          <MdLanguage fontSize={16} />
          www.unpod.ai
        </a>
        <a href="tel:+919718913131">
          <MdLocalPhone fontSize={16} />
          +91 97189 13131
        </a>
        <a href="mailto:info@unpod.ai">
          <MdMailOutline fontSize={16} />
          info@unpod.ai
        </a>
      </StyledFooterBar>
    </StyledRoot>
  );
};

export default UpAgent;
