'use client';
import React, { useEffect, useState } from 'react';
import { Button, Card, Typography } from 'antd';
import {
  StyledContainer,
  StylesButtonWrapper,
  StylesImageWrapper,
} from './index.styled';
import {
  getDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useRouter } from 'next/navigation';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import AppImage from '@unpod/components/next/AppImage';
import { useAppHistory } from '@unpod/providers/AppHistoryProvider';
import { setOrgHeader } from '@unpod/services';
import AppLink from '@unpod/components/next/AppLink';
import { isEmptyObject } from '@unpod/helpers/GlobalHelper';
import { useIntl } from 'react-intl';
import type { Organization, Spaces } from '@unpod/constants/types';

const { Paragraph, Title } = Typography;

const JoinOrg = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { historyOrg, historySpace, nextStep } = useAppHistory() as {
    historyOrg?: Organization | null;
    historySpace?: Spaces | null;
    nextStep?: string | null;
  };
  const { updateAuthUser, setActiveOrg } = useAuthActionsContext();
  const { user } = useAuthContext();
  const router = useRouter();
  const { formatMessage } = useIntl();

  const [requestedOrg, setRequestedHub] = useState<Organization | null>(null);
  const mergeOrganizationList = (
    list: Organization[] | undefined,
    nextOrg?: Organization,
  ): Organization[] => {
    if (!nextOrg) {
      return list || [];
    }
    const trimmed = (list || []).filter(
      (item) => item.domain_handle !== nextOrg.domain_handle,
    );
    return [...trimmed, nextOrg];
  };

  useEffect(() => {
    if (historyOrg) {
      setRequestedHub(historyOrg);
    } else if (user?.organization) {
      setRequestedHub(user?.organization);
    }
  }, [historyOrg, user?.organization]);

  const onJoinClick = () => {
    if (!user) {
      return;
    }
    const path = process.env.productId === 'unpod.dev' ? 'dashboard' : 'org';
    if (
      (nextStep === 'join-org' || nextStep === 'join-space') &&
      (requestedOrg || historySpace)
    ) {
      let requestUrl = `spaces/invite/join/${historySpace?.invite_token ?? ''}/`;

      if (nextStep === 'join-org') {
        requestUrl = `organization/join/${requestedOrg?.invite_token ?? ''}/`;
      }

      getDataApi<Organization | Spaces>(requestUrl, infoViewActionsContext)
        .then((data) => {
          const payloadData = data?.data;
          if (
            !payloadData ||
            isEmptyObject(payloadData as Record<string, unknown>)
          ) {
            infoViewActionsContext.showMessage(data?.message || '');
            router.push(`/org/`);
            return;
          }
          infoViewActionsContext.showMessage(data.message || '');

          if (nextStep === 'join-org') {
            const org = payloadData as Organization;
            if (!org?.domain_handle) {
              return;
            }
            updateAuthUser({
              ...user,
              organization: org,
              organization_list: mergeOrganizationList(
                user.organization_list,
                org,
              ),
            });
            setOrgHeader(org.domain_handle);
            getDataApi<Organization>(
              `organization/detail/${org.domain_handle}/`,
              infoViewActionsContext,
            )
              .then((data) => {
                updateAuthUser({
                  ...user,
                  organization_list: mergeOrganizationList(
                    user.organization_list,
                    data.data,
                  ),
                });
                setActiveOrg(data.data);
                router.push(`/${path}/`);
              })
              .catch((error) => {
                const payload = error as { message?: string };
                infoViewActionsContext.showError(payload.message || '');
              });
          } else if (nextStep === 'join-space') {
            const space = payloadData as Spaces;
            const domainHandle = space?.organization?.domain_handle;
            if (!domainHandle) {
              return;
            }
            updateAuthUser({
              ...user,
              organization: space.organization,
              active_space: space,
              organization_list: mergeOrganizationList(
                user.organization_list,
                space.organization,
              ),
            });
            setOrgHeader(domainHandle);
            getDataApi<Organization>(
              `organization/detail/${domainHandle}/`,
              infoViewActionsContext,
            )
              .then((orgData) => {
                updateAuthUser({
                  ...user,

                  active_space: space,
                  organization_list: mergeOrganizationList(
                    user.organization_list,
                    orgData.data,
                  ),
                });
                setActiveOrg(orgData.data);
                router.push(`/spaces/${space.slug}/call/`);
              })
              .catch((error) => {
                const payload = error as { message?: string };
                infoViewActionsContext.showError(payload.message || '');
              });
          }
        })
        .catch((error) => {
          const payload = error as { message?: string };
          infoViewActionsContext.showError(payload.message || '');
        });
    } else if (
      user?.invite_type === 'organization' &&
      requestedOrg?.invite_token
    ) {
      const requestUrl = `organization/join/${requestedOrg?.invite_token}/`;

      getDataApi<Organization>(requestUrl, infoViewActionsContext)
        .then((data) => {
          const payloadData = data?.data;
          if (
            !payloadData ||
            isEmptyObject(payloadData as Record<string, unknown>)
          ) {
            infoViewActionsContext.showMessage(data?.message || '');
            router.push(`/org/`);
            return;
          }
          infoViewActionsContext.showMessage(data.message || '');
          const currentDomain = user?.organization?.domain_handle;
          if (!currentDomain) {
            return;
          }
          setOrgHeader(currentDomain);
          getDataApi<Organization>(
            `organization/detail/${currentDomain}/`,
            infoViewActionsContext,
          )
            .then((data) => {
              updateAuthUser({
                ...user,
                organization_list: mergeOrganizationList(
                  user.organization_list,
                  data.data,
                ),
              });
              setActiveOrg(data.data);
              router.push(`/${path}/`);
            })
            .catch((error) => {
              const payload = error as { message?: string };
              infoViewActionsContext.showError(payload.message || '');
            });
        })
        .catch((error) => {
          const payload = error as { message?: string };
          infoViewActionsContext.showError(payload.message || '');
        });
    } else if (user?.invite_type === 'space') {
      const requestUrl = `spaces/invite/join/${historySpace?.invite_token ?? ''}/`;
      getDataApi<Spaces>(requestUrl, infoViewActionsContext)
        .then((spaceData) => {
          const payloadData = spaceData?.data;
          if (
            !payloadData ||
            isEmptyObject(payloadData as Record<string, unknown>)
          ) {
            infoViewActionsContext.showMessage(spaceData?.message || '');
            router.push(`/org/`);
            return;
          }
          infoViewActionsContext.showMessage(spaceData.message || '');
          const domainHandle = payloadData?.organization?.domain_handle;
          if (!domainHandle) {
            return;
          }
          setOrgHeader(domainHandle);
          getDataApi<Organization>(
            `organization/detail/${domainHandle}/`,
            infoViewActionsContext,
          )
            .then((orgData) => {
              updateAuthUser({
                ...user,
                active_space: payloadData,
                organization_list: mergeOrganizationList(
                  user.organization_list,
                  orgData.data,
                ),
              });
              setActiveOrg(orgData.data);
              router.push(`/spaces/${payloadData?.slug}/call/`);
            })
            .catch((error) => {
              const payload = error as { message?: string };
              infoViewActionsContext.showError(payload.message || '');
            });
        })
        .catch((error) => {
          const payload = error as { message?: string };
          infoViewActionsContext.showError(payload.message || '');
        });
    } else {
      const currentDomain = user?.organization?.domain_handle;
      if (!currentDomain) {
        return;
      }
      const requestUrl = `organization/subscribe/my-organization/${currentDomain}/`;
      getDataApi<Organization>(requestUrl, infoViewActionsContext)
        .then((data) => {
          const payloadData = data?.data;
          if (
            !payloadData ||
            isEmptyObject(payloadData as Record<string, unknown>)
          ) {
            infoViewActionsContext.showMessage(data?.message || '');
            router.push(`/org/`);
            return;
          }
          infoViewActionsContext.showMessage(data.message || '');
          setOrgHeader(currentDomain);
          getDataApi<Organization>(
            `organization/detail/${currentDomain}/`,
            infoViewActionsContext,
          )
            .then((data) => {
              updateAuthUser({
                ...user,
                organization_list: mergeOrganizationList(
                  user.organization_list,
                  data.data,
                ),
              });
              setActiveOrg(data.data);
              router.push(`/${path}/`);
            })
            .catch((error) => {
              const payload = error as { message?: string };
              infoViewActionsContext.showError(payload.message || '');
            });
        })
        .catch((error) => {
          const payload = error as { message?: string };
          infoViewActionsContext.showError(payload.message || '');
        });
    }
  };

  return (
    <AppPageLayout layout="full">
      <StyledContainer>
        <Card>
          <StylesImageWrapper>
            <AppImage
              src={
                requestedOrg?.logo
                  ? `${requestedOrg?.logo}?tr=w-110,h-110`
                  : '/images/logo_avatar.png'
              }
              alt="logo"
              height={80}
              width={80}
              objectFit="cover"
            />
          </StylesImageWrapper>

          <Title>
            {nextStep === 'join-space'
              ? historySpace?.name
              : requestedOrg?.name}
          </Title>
          <Paragraph>
            {formatMessage(
              { id: 'joinOrg.paragraph' },
              {
                name:
                  nextStep === 'join-space'
                    ? historySpace?.name
                    : requestedOrg?.name,
                type: nextStep === 'join-space' ? 'space' : 'organization',
              },
            )}
          </Paragraph>
          {requestedOrg && (
            <Paragraph strong>
              {formatMessage(
                { id: 'joinOrg.invitedFor' },
                {
                  name:
                    nextStep === 'join-space'
                      ? historySpace?.name
                      : requestedOrg?.name,
                },
              )}
            </Paragraph>
          )}

          <StylesButtonWrapper>
            <Button type="primary" onClick={onJoinClick} block>
              {nextStep === 'join-space'
                ? formatMessage({ id: 'joinOrg.joinSpace' })
                : formatMessage({ id: 'joinOrg.joinOrganization' })}
            </Button>
          </StylesButtonWrapper>

          <Paragraph>
            {formatMessage({ id: 'joinOrg.agreement' })}{' '}
            <AppLink href="/privacy-policy/">
              {formatMessage({ id: 'common.privacy' })}
            </AppLink>
            {formatMessage({ id: 'auth.and' })}{' '}
            <AppLink href="/terms-and-conditions/">
              {formatMessage({ id: 'common.terms' })}
            </AppLink>{' '}
            {formatMessage({ id: 'joinOrg.agreementSuffix' })}
          </Paragraph>
        </Card>
      </StyledContainer>
    </AppPageLayout>
  );
};

export default JoinOrg;
