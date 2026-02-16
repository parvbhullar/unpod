'use client';
import React from 'react';
import {
  StyledButton,
  StyledCenterContainer,
  StyledContainer,
  StyledHeader,
  StyledLeftContainer,
  StyledMainTitle,
  StyledRightContainer,
  StyledTitleBlock,
} from './index.styled';
import AppToggleSidebar from '../AppToggleSidebar';
import { useAuthContext } from '@unpod/providers';
import { useRouter } from 'next/navigation';
import ListingOptions from './ListingOptions';

export const AppHeaderButton = StyledButton;

type AppPageHeaderProps = {
  leftOptions?: React.ReactNode;
  rightOptions?: React.ReactNode;
  centerOptions?: React.ReactNode;
  pageTitle?: React.ReactNode;
  titleIcon?: React.ReactNode;
  isListingPage?: boolean;
  hideToggleBtn?: boolean;
  hideAuthBtn?: boolean;
  children?: React.ReactNode;
};

const AppPageHeader: React.FC<AppPageHeaderProps> = ({
  leftOptions,
  rightOptions,
  centerOptions,
  pageTitle,
  titleIcon,
  isListingPage,
  hideToggleBtn,
  hideAuthBtn,
  children,
}) => {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthContext();

  return (
    <StyledHeader>
      {children || (
        <StyledContainer $hasCenter={!!centerOptions}>
          <StyledLeftContainer>
            {!hideToggleBtn && <AppToggleSidebar />}

            {pageTitle &&
              (typeof pageTitle === 'string' ? (
                <StyledTitleBlock>
                  {titleIcon}
                  <StyledMainTitle
                    level={1}
                    className="mb-0"
                    ellipsis={{ rows: 1 }}
                  >
                    {pageTitle}
                  </StyledMainTitle>
                </StyledTitleBlock>
              ) : (
                pageTitle
              ))}

            {leftOptions}
          </StyledLeftContainer>

          {centerOptions && (
            <StyledCenterContainer>{centerOptions}</StyledCenterContainer>
          )}

          <StyledRightContainer>
            {isListingPage && <ListingOptions />}
            {rightOptions}
            {!isAuthenticated && !isLoading && !hideAuthBtn && (
              <React.Fragment>
                <StyledButton
                  type="primary"
                  size="small"
                  shape="round"
                  onClick={() => router.push('/auth/signin/')}
                >
                  Sign In
                </StyledButton>

                <StyledButton
                  type="primary"
                  size="small"
                  shape="round"
                  onClick={() => router.push('/auth/signup/')}
                >
                  Sign Up
                </StyledButton>
              </React.Fragment>
            )}
          </StyledRightContainer>
        </StyledContainer>
      )}
    </StyledHeader>
  );
};

export default AppPageHeader;
