import { Fragment } from 'react';
import { Space } from 'antd';
import AppLink from '@unpod/components/next/AppLink';
import AppImage from '@unpod/components/next/AppImage';
import {
  StyledButton,
  StyledHeader,
  StyledHeaderContainer,
  StyledLogo,
} from './index.styled';
import { useRouter } from 'next/navigation';
import {
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useMediaQuery } from 'react-responsive';
import { MdLockOpen } from 'react-icons/md';
import { RiDiscordFill } from 'react-icons/ri';
import { GrDocumentText } from 'react-icons/gr';
import { TabWidthQuery } from '@unpod/constants';
import { useIntl } from 'react-intl';

type LayoutHeaderProps = {
  headerBg?: string;
};

const LayoutHeader = ({ headerBg }: LayoutHeaderProps) => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const infoViewActionsContext = useInfoViewActionsContext();
  const { logoutUser } = useAuthActionsContext();
  const { isAuthenticated } = useAuthContext();
  const router = useRouter();
  const { formatMessage } = useIntl();

  const onSignInClick = async () => {
    router.push('/auth/signin');
  };

  const onLogoutClick = () => {
    (logoutUser() as Promise<{ message?: string }>)
      .then((response: { message?: string }) => {
        infoViewActionsContext.showMessage(response.message || 'Logged out');
        router.push('/auth/signin');
      })
      .catch((response: { message?: string }) => {
        infoViewActionsContext.showError(response.message || 'Logout failed');
      });
  };

  return (
    <StyledHeader $headerBg={headerBg}>
      <StyledHeaderContainer>
        <StyledLogo>
          <AppLink href="/">
            <AppImage
              src="/images/unpod/logo.svg"
              alt="unpod logo"
              height={38}
              width={120}
            />
          </AppLink>
        </StyledLogo>

        {/*{!isTabletOrMobile && (
          <StyledMenu>
            {menus.map((menuItem) => (
              <li key={menuItem.id}>
                <AppLink href={menuItem.route} scroll={false}>
                  {menuItem.title}
                </AppLink>
              </li>
            ))}
          </StyledMenu>
        )}*/}

        <Space>
          {process.env.productId === 'unpod.dev' && (
            <StyledButton
              type="text"
              shape="circle"
              href="https://docs.unpod.dev/"
              target="_blank"
              rel="noopener noreferrer"
              size={isTabletOrMobile ? 'small' : 'middle'}
              title={formatMessage({ id: 'common.documentation' })}
            >
              <GrDocumentText fontSize={18} />
            </StyledButton>
          )}
          {/* {process.env.productId === 'unpod.ai' && (
            <StyledButton
              type="text"
              shape="circle"
              href="/download/"
              size={isTabletOrMobile ? 'small' : 'middle'}
              title={formatMessage({ id: 'common.download' })}
            >
              <HiOutlineDownload fontSize={20} />
            </StyledButton>
          )}*/}
          <StyledButton
            type="text"
            shape="circle"
            href="https://docs.unpod.dev/"
            target="_blank"
            size={isTabletOrMobile ? 'small' : 'middle'}
            title={formatMessage({ id: 'common.documentation' })}
          >
            <GrDocumentText fontSize={18} />
          </StyledButton>
          <StyledButton
            type="text"
            shape="circle"
            href="https://discord.gg/7kQ4ewNSHZ"
            target="_blank"
            size={isTabletOrMobile ? 'small' : 'middle'}
            title={formatMessage({ id: 'common.discord' })}
          >
            <RiDiscordFill fontSize={24} />
          </StyledButton>
          {isAuthenticated ? (
            <Fragment>
              {/*{user?.current_step === 'join_organization' ||
              user?.current_step === 'organization' ? (
                <StyledButton
                  type="primary"
                  shape="round"
                  size={isTabletOrMobile ? 'small' : 'middle'}
                  onClick={joinOrCreateHub}
                >
                  {isTabletOrMobile ? (
                    <MdOutlineWorkspaces fontSize={18} />
                  ) : isEmptyObject(user?.organization) ? (
                    'Create Organization'
                  ) : (
                    'Join Organization'
                  )}
                </StyledButton>
              ) : (
                <StyledButton
                  type="primary"
                  shape="round"
                  size={isTabletOrMobile ? 'small' : 'middle'}
                  onClick={goToMyHub}
                >
                  {isTabletOrMobile ? (
                    <MdOutlineWorkspaces fontSize={18} />
                  ) : (
                    'My Organization'
                  )}
                </StyledButton>
              )}*/}

              <StyledButton
                type="primary"
                shape="round"
                size={isTabletOrMobile ? 'small' : 'middle'}
                onClick={onLogoutClick}
              >
                {isTabletOrMobile ? (
                  <MdLockOpen fontSize={18} />
                ) : (
                  formatMessage({ id: 'common.logout' })
                )}
              </StyledButton>
            </Fragment>
          ) : (
            <Fragment>
              <StyledButton
                type="primary"
                shape="round"
                size={isTabletOrMobile ? 'small' : 'middle'}
                onClick={onSignInClick}
              >
                {isTabletOrMobile ? (
                  <MdLockOpen fontSize={18} />
                ) : (
                  formatMessage({ id: 'auth.signIn' })
                )}
              </StyledButton>

              {/*<StyledButton
                type="primary"
                shape="round"
                size={isTabletOrMobile ? 'small' : 'middle'}
                onClick={onSignUpClick}
              >
                {isTabletOrMobile ? <RiUserLine fontSize={18} /> : 'Sign Up'}
              </StyledButton>*/}
            </Fragment>
          )}
          {/*{isTabletOrMobile && (
            <Dropdown
              menu={{
                items: menus.map((menuItem) =>
                  getItem(menuItem.title, menuItem.id, menuItem.route)
                ),
              }}
              trigger={['click']}
            >
              <StyledButton
                type="primary"
                size="small"
                icon={<MdMenu fontSize={18} />}
                ghost
              />
            </Dropdown>
          )}*/}
        </Space>
      </StyledHeaderContainer>
    </StyledHeader>
  );
};

export default LayoutHeader;
