import React, {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button, Tooltip } from 'antd';
import {
  getDataApi,
  useAppSpaceContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { getPostIcon } from '@unpod/helpers/PermissionHelper';
import {
  MdAddCircleOutline,
  MdOutlineArrowDropDown,
  MdOutlineArrowDropUp,
  MdOutlineWorkspaces,
  MdRefresh,
} from 'react-icons/md';
import {
  COLLECTION_TYPE_DATA,
  SPACE_VISIBLE_CONTENT_TYPES,
} from '@unpod/constants';
import AppLoader from '../AppLoader';
import AppNewSpace from '../../modules/AppNewSpace';
import AppCustomMenus from '../AppCustomMenus';
import {
  StyledAddButton,
  StyledIconWrapper,
  StyledInput,
  StyledInputWrapper,
  StyledLabel,
  StyledLoader,
  StyledMainTitle,
  StyledMenusContainer,
  StyledTitleBlock,
  StyledTitleContent,
  StyledTitleWrapper,
} from './index.styled';
import { AppPopover } from '../../antd';
import { useIntl } from 'react-intl';
import {
  getStatusOptionsFromConfig,
  type StatusConfigValue,
  type StatusOption,
} from '@unpod/helpers/LocalizationFormatHelper';

type SpaceItem = {
  slug: string;
  name: string;
  content_type: string;
  privacy_type?: string;};

type MenuItem = {
  label: string;
  key: string;
  icon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onClick?: () => void;
  contentType: string;};

type AppSpaceHeaderMenusProps = {
  addNew?: boolean;
  setAddNew: (open: boolean) => void;
  isContentHeader?: boolean;};

const AppSpaceHeaderMenus = ({
  addNew = false,
  setAddNew,
  isContentHeader = false,
}: AppSpaceHeaderMenusProps) => {
  const { formatMessage } = useIntl();
  const { currentSpace, activeTab } = useAppSpaceContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { isAuthenticated, activeOrg } = useAuthContext();
  const router = useRouter();
  const { spaceSlug } = useParams<{ spaceSlug?: string }>();
  const [loading, setLoading] = useState(false);
  const [spaces, setSpaces] = useState<SpaceItem[]>([]);
  const [search, setSearch] = useState('');
  const [openPopover, setOpenPopover] = useState(false);
  const visibleTypes = SPACE_VISIBLE_CONTENT_TYPES as unknown as string[];

  const getSpaces = useCallback(() => {
    setLoading(true);
    (
      getDataApi(`spaces/`, infoViewActionsContext, {
        case: 'all',
      }) as Promise<{ data: SpaceItem[] }>
    )
      .then((response) => {
        setSpaces(
          response.data.filter((space) =>
            visibleTypes.includes(space.content_type),
          ),
        );
        setLoading(false);
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
        setLoading(false);
      });
  }, [infoViewActionsContext, activeOrg?.domain_handle, visibleTypes]);

  useEffect(() => {
    if (isAuthenticated) {
      getSpaces();
    }
  }, [isAuthenticated, getSpaces]);

  const onMenuClick = useCallback(
    (slug: string) => {
      setOpenPopover(false);
      if (spaceSlug !== slug) {
        router.push(`/spaces/${slug}/${activeTab || 'chat'}`);
      }
    },
    [spaceSlug, router, activeTab],
  );

  const items = useMemo<MenuItem[]>(() => {
    const contentTypeOptions = getStatusOptionsFromConfig(
      COLLECTION_TYPE_DATA as unknown as Record<string, StatusConfigValue>,
      formatMessage,
    ) as StatusOption[];

    if (search) {
      return spaces
        .filter((space) =>
          space.name.toLowerCase().includes(search.toLowerCase()),
        )
        .map((space) => {
          const contentType = contentTypeOptions.find(
            (item) => item.id === space.content_type,
          );

          return {
            label: space.name,
            key: space.slug,
            icon: getPostIcon(space.privacy_type ?? ''),
            rightIcon: space.content_type !== 'general' && (
              <StyledLabel>{contentType?.name}</StyledLabel>
            ),
            onClick: () => onMenuClick(space.slug),
            contentType: space.content_type,
          };
        });
    }

    return spaces.map((space) => {
      const contentType = contentTypeOptions.find(
        (item) => item.id === space.content_type,
      );
      return {
        label: space.name,
        key: space.slug,
        icon: getPostIcon(space.privacy_type ?? ''),
        rightIcon: space.content_type !== 'general' && (
          <StyledLabel>{contentType?.name}</StyledLabel>
        ),
        onClick: () => onMenuClick(space.slug),
        contentType: space.content_type,
      };
    });
  }, [formatMessage, spaces, search, onMenuClick]);

  const onCreateClick = () => {
    setOpenPopover(false);
    setAddNew(true);
  };

  const onSpaceCreated = (response: { data: { slug: string } }) => {
    getSpaces();
    router.push(`/spaces/${response.data.slug}`);
  };

  return (
    <Fragment>
      <StyledTitleBlock>
        {currentSpace?.name ? (
          <MdOutlineWorkspaces fontSize={isContentHeader ? 26 : 21} />
        ) : (
          <MdOutlineWorkspaces fontSize={isContentHeader ? 26 : 21} />
        )}

        {isAuthenticated ? (
          <StyledTitleWrapper>
            <AppPopover
              open={openPopover}
              content={
                <StyledMenusContainer>
                  <StyledInputWrapper>
                    <StyledInput
                      placeholder={formatMessage({ id: 'common.searchHere' })}
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                    />

                    <Tooltip title={formatMessage({ id: 'common.refresh' })}>
                      <Button
                        type="text"
                        size="small"
                        icon={<MdRefresh fontSize={24} />}
                        onClick={() => getSpaces()}
                        loading={loading}
                      />
                    </Tooltip>
                  </StyledInputWrapper>

                  <AppCustomMenus
                    items={
                      items &&
                      items.filter((item) =>
                        visibleTypes.includes(item.contentType),
                      )
                    }
                    activeKeys={spaceSlug ? [spaceSlug] : []}
                  />

                  {loading && (
                    <>
                      <StyledLoader
                        style={{
                          position: 'absolute',
                          inset: 0,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background: 'rgba(255,255,255,0.6)',
                          zIndex: 100,
                        }}
                      >
                        <AppLoader
                          position="relative"
                          style={{ backgroundColor: 'transparent' }}
                        />
                      </StyledLoader>
                    </>
                  )}

                  <StyledAddButton onClick={() => onCreateClick()}>
                    <MdAddCircleOutline fontSize={16} />
                    <span>{formatMessage({ id: 'space.addNew' })}</span>
                  </StyledAddButton>
                </StyledMenusContainer>
              }
              styles={{ root: { zIndex: 1000 } }}
              onOpenChange={setOpenPopover}
            >
              <StyledTitleContent>
                <StyledMainTitle
                  className={isContentHeader ? 'smart-heading' : undefined}
                >
                  {String(currentSpace?.name || 'Space')}
                </StyledMainTitle>

                {/*  {currentSpace?.content_type !== 'general' && document && (
                  <StyledLabel color={theme.palette.primary}>
                    {document?.name || 'General'}
                  </StyledLabel>
                )}*/}

                <StyledIconWrapper>
                  <MdOutlineArrowDropUp fontSize={isContentHeader ? 20 : 18} />
                  <MdOutlineArrowDropDown
                    fontSize={isContentHeader ? 20 : 18}
                  />
                </StyledIconWrapper>
              </StyledTitleContent>
            </AppPopover>

            {/*{currentSpace?.name && <AppBreadCrumb items={breadcrumb} />}*/}
          </StyledTitleWrapper>
        ) : (
          <StyledMainTitle>
            {String(currentSpace?.name || 'Space')}
          </StyledMainTitle>
        )}
      </StyledTitleBlock>

      <AppNewSpace
        content_type={
          typeof currentSpace?.content_type === 'string'
            ? currentSpace.content_type
            : undefined
        }
        openForm={addNew}
        setFormOpen={setAddNew}
        onSpaceCreated={onSpaceCreated}
      />
    </Fragment>
  );
};

export default AppSpaceHeaderMenus;
