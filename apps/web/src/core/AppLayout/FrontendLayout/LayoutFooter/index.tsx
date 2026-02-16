import {
  StyledBottomContainer,
  StyledCopyright,
  StyledFooter,
  StyledFooterContainer,
  StyledLinkWrapper,
} from './index.styled';
import { FloatButton, theme, Typography } from 'antd';
import AppLink from '@unpod/components/next/AppLink';
import { RiArrowUpLine } from 'react-icons/ri';

const today = new Date();

const LayoutFooter = () => {
  const { token } = theme.useToken();

  return (
    <StyledFooter id="contact">
      <StyledFooterContainer>
        <StyledBottomContainer>
          <StyledCopyright>
            <Typography.Paragraph>
              © {today.getFullYear()} Unpod.dev. All rights reserved
            </Typography.Paragraph>
          </StyledCopyright>
          {/* <a href="https://elevenlabs.io/text-to-speech">
            <AppImage
              src="https://storage.googleapis.com/eleven-public-cdn/images/elevenlabs-grants-logo.png"
              alt="Text to Speech"
              height={40}
              width={250}
            />
          </a>*/}
          <StyledLinkWrapper>
            <AppLink href="/privacy-policy/">Privacy Policy</AppLink>
            <span style={{ color: token.colorPrimary }}>|</span>
            <AppLink href="/terms-and-conditions/">Terms & Conditions</AppLink>
          </StyledLinkWrapper>
        </StyledBottomContainer>

        <FloatButton.BackTop
          type="primary"
          icon={<RiArrowUpLine fontSize={20} />}
        />
      </StyledFooterContainer>
    </StyledFooter>
  );
};

export default LayoutFooter;
