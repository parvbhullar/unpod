'use client';
import React, { Fragment } from 'react';
import { useIntl } from 'react-intl';
import { MdOutlineVerifiedUser } from 'react-icons/md';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import { useAuthContext } from '@unpod/providers';
import EditProfile from './EditProfile';
import ChangePassword from './ChangePassword';
import LanguagePreference from './LanguagePreference';
import PageBaseHeader from '@unpod/components/common/AppPageLayout/layouts/ThreeColumnPageLayout/PageBaseHeader';
import { StyledContainer, StyledTabs } from './index.styled';
import { SettingSkeleton } from '@unpod/skeleton';

const Profile = () => {
  const { formatMessage } = useIntl();
  const { user } = useAuthContext();

  // if (!user) return ;

  return (
    <Fragment>
      <PageBaseHeader
        pageTitle={formatMessage({ id: 'profile.profileSettings' })}
        titleIcon={<MdOutlineVerifiedUser fontSize={21} />}
        hideToggleBtn
      />

      <AppPageContainer>
        {!user ? (
          <SettingSkeleton />
        ) : (
          <StyledContainer>
            <StyledTabs
              defaultActiveKey="account"
              items={[
                {
                  label: formatMessage({ id: 'profile.editProfile' }),
                  key: 'edit-profile',
                  children: <EditProfile user={user} />,
                },
                {
                  label: formatMessage({ id: 'profile.changePassword' }),
                  key: 'change-password',
                  children: <ChangePassword />,
                },
                {
                  label: formatMessage({ id: 'profile.languagePreference' }),
                  key: 'language-preference',
                  children: <LanguagePreference user={user} />,
                },
              ]}
            />
          </StyledContainer>
        )}
      </AppPageContainer>
    </Fragment>
  );
};

export default Profile;
