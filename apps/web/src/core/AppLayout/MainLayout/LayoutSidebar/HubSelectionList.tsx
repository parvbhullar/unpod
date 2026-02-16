'use client';
import { useMemo, useState } from 'react';
import { Avatar, type MenuProps, Spin } from 'antd';
import { getFirstLetter } from '@unpod/helpers/StringHelper';
import {
  getDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useRouter } from 'next/navigation';
import { RiOrganizationChart } from 'react-icons/ri';
import { useTheme } from 'styled-components';
import { isEmptyObject } from '@unpod/helpers/GlobalHelper';
import { setOrgHeader } from '@unpod/services';
import { StyledHubMenus, StyledOverlayLoader } from './index.styled';
import type { Organization } from '@unpod/constants/types';

type HubSelectionListProps = {
  setOpenOrgMenu: (open: boolean) => void;
};

const HubSelectionList = ({ setOpenOrgMenu }: HubSelectionListProps) => {
  const router = useRouter();
  const infoViewActionsContext = useInfoViewActionsContext();
  const theme = useTheme();
  const { user, activeOrg } = useAuthContext();
  const { setActiveOrg } = useAuthActionsContext();
  const [isChangingHub, setIsChangingHub] = useState(false);

  const onChangeHub = (org: Organization) => {
    setIsChangingHub(true);
    setOrgHeader(org?.domain_handle);
    getDataApi<Organization>(
      `organization/detail/${org?.domain_handle}/`,
      infoViewActionsContext,
      {},
    )
      .then((response) => {
        const { data } = response;
        setIsChangingHub(false);
        setOpenOrgMenu(false);
        setOrgHeader(data?.domain_handle);
        setActiveOrg(data);
      })
      .catch(() => {
        setIsChangingHub(false);
      });
  };

  const items = useMemo<MenuProps['items']>(() => {
    let organizations = user?.organization_list;

    if (!activeOrg?.joined) {
      organizations = user?.organization_list?.filter(
        (org) => org?.domain_handle !== activeOrg?.domain_handle,
      );
    }

    if (organizations?.length === 0) {
      return [
        isEmptyObject(user?.organization ?? {})
          ? {
              key: 'create-org',
              label: 'Create an Organization',
              icon: (
                <Avatar
                  style={{
                    backgroundColor: theme.palette.primary,
                    minWidth: 32,
                  }}
                >
                  <RiOrganizationChart fontSize={20} />
                </Avatar>
              ),
              onClick: () => router.push(`/create-org/`),
            }
          : {
              key: 'join-org',
              label: 'Join an Organization',
              icon: (
                <Avatar
                  style={{
                    backgroundColor: theme.palette.primary,
                    minWidth: 32,
                  }}
                >
                  <RiOrganizationChart fontSize={20} />
                </Avatar>
              ),
              onClick: () => router.push(`/join-org/`),
            },
      ];
    }

    return organizations?.map((org) => {
      const key = org?.domain_handle || '';
      return {
        label: org?.name || '',
        key,
        icon: (
          <Avatar
            style={{
              backgroundColor: org?.logo ? '' : org?.color,
              minWidth: 32,
            }}
            src={org?.logo}
            shape="square"
          >
            {getFirstLetter(org?.name)}
          </Avatar>
        ),
        onClick: () => onChangeHub(org),
      };
    }) as MenuProps['items'];
  }, [user?.organization_list, activeOrg]);

  return (
    <>
      <StyledHubMenus
        mode="inline"
        selectedKeys={activeOrg?.domain_handle ? [activeOrg.domain_handle] : []}
        items={items}
      />

      {isChangingHub ? (
        <StyledOverlayLoader>
          <Spin />
        </StyledOverlayLoader>
      ) : null}
    </>
  );
};

export default HubSelectionList;
