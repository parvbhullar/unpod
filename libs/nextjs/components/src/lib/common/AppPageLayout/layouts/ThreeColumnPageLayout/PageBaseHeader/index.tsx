'use client';
import type {ReactNode} from 'react';

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
import AppToggleSidebar from '../../../../AppToggleSidebar';
import {useAuthContext} from '@unpod/providers';
import ListingOptions from './ListingOptions';
import {useRouter} from 'next/navigation';

type PageBaseHeaderProps = {
  leftOptions?: ReactNode;
  rightOptions?: ReactNode;
  centerOptions?: ReactNode;
  pageTitle?: ReactNode;
  titleIcon?: ReactNode;
  isListingPage?: boolean;
  hideToggleBtn?: boolean;
  hideAuthBtn?: boolean;
  children?: ReactNode;
};

const PageBaseHeader = ({
                          leftOptions,
                          rightOptions,
                          centerOptions,
                          pageTitle,
                          titleIcon,
                          isListingPage,
                          hideToggleBtn,
                          hideAuthBtn,
                          children,
                        }: PageBaseHeaderProps) => {
  const router = useRouter();
  const {isAuthenticated, isLoading} = useAuthContext();
  // const [isScrolled, setScrolled] = useState(false);

  /*useEffect(() => {
    window.addEventListener('scroll', function () {
      const scrollPos = window.scrollY;
      setScrolled(scrollPos > 20);
    });
  }, []);*/

  return (
    <StyledHeader>
      {children || (
        <StyledContainer $hasCenter={!!centerOptions}>
          <StyledLeftContainer>
            {!hideToggleBtn && <AppToggleSidebar/>}

            {pageTitle &&
              (typeof pageTitle === 'string' ? (
                <StyledTitleBlock>
                  {titleIcon}
                  <StyledMainTitle
                    level={1}
                    className="mb-0"
                    ellipsis={{rows: 1}}
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

          {/*<StyledCenterContainer>
            {pageTitle && (
              <StyledTitleWrapper $isScrolled={isScrolled}>
                {typeof pageTitle === 'string' ? (
                  <StyledMainTitle
                    level={1}
                    className="mb-0"
                    ellipsis={{ rows: 1 }}
                  >
                    {pageTitle}
                  </StyledMainTitle>
                ) : (
                  pageTitle
                )}
              </StyledTitleWrapper>
            )}
          </StyledCenterContainer>*/}

          <StyledRightContainer>
            {isListingPage && <ListingOptions/>}
            {rightOptions}
            {!isAuthenticated && !isLoading && !hideAuthBtn && (
              <>
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
              </>
            )}
          </StyledRightContainer>
        </StyledContainer>
      )}
    </StyledHeader>
  );
};

export default PageBaseHeader;
