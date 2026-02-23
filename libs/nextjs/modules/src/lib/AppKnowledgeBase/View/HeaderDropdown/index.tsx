'use client';
import {Fragment, useCallback, useEffect, useMemo, useState} from 'react';
import AppLink from '@unpod/components/next/AppLink';
import {useParams, useRouter} from 'next/navigation';
import {Button, Tooltip} from 'antd';
import {getDataApi, useAuthContext, useInfoViewActionsContext,} from '@unpod/providers';
import {getPostIcon} from '@unpod/helpers/PermissionHelper';
import {MdAddCircleOutline, MdOutlineArrowDropDown, MdOutlineArrowDropUp, MdRefresh,} from 'react-icons/md';
import {BsDatabase} from 'react-icons/bs';
import AppCustomMenus from '@unpod/components/common/AppCustomMenus';
import {AppBreadCrumb, AppBreadCrumbTitle, AppPopover,} from '@unpod/components/antd';
import {COLLECTION_TYPE_DATA} from '@unpod/constants';
import {useTheme} from 'styled-components';
import AppNewKb from '@unpod/components/modules/AppCreateKb';
import AppLoader from '@unpod/components/common/AppLoader';
import {
  StyledAddButton,
  StyledDropdownArrow,
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
import {useIntl} from 'react-intl';
import {getStatusOptionsFromConfig} from '@unpod/helpers/LocalizationFormatHelper';

type KnowledgeBaseItem = {
  name?: string;
  slug?: string;
  type?: string;
  privacy_type?: string;
  content_type?: string;
};

type HeaderDropdownProps = {
  pageTitle: any;
  currentKb: any;
  setCurrentKb: (kb: any) => void;
  addNew: boolean;
  setAddNew: (open: boolean) => void;
};

const HeaderDropdown = ({
                          pageTitle,
                          currentKb,
                          setCurrentKb,
                          addNew,
                          setAddNew,
                        }: HeaderDropdownProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {isAuthenticated} = useAuthContext();
  const router = useRouter();
  const {kbSlug} = useParams() as { kbSlug?: string | string[] };
  const kbSlugValue = Array.isArray(kbSlug) ? kbSlug[0] : kbSlug;
  const theme = useTheme();
  const {formatMessage} = useIntl();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<KnowledgeBaseItem[]>([]);
  const [search, setSearch] = useState('');
  const [openPopover, setOpenPopover] = useState(false);

  const getKnowledgeBases = useCallback(() => {
    setLoading(true);
    getDataApi(`spaces/`, infoViewActionsContext, {
      space_type: 'knowledge_base',
      case: 'all',
    })
      .then((response: any) => {
        setData(response.data || []);
        setLoading(false);

        if (!kbSlugValue && response.data?.length) {
          getDataApi(
            `spaces/${response.data[0]?.slug}/`,
            infoViewActionsContext,
          )
            .then((detailRes: any) => {
              setCurrentKb?.(detailRes.data);
            })
            .catch((error: any) => {
              console.log('error', error);
              if (error.status_code === 206) {
                setCurrentKb?.(error.data);
              } else {
                infoViewActionsContext.showError(error.message);
              }
            });
        }
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
        setLoading(false);
      });
  }, [kbSlug, infoViewActionsContext, setCurrentKb]);

  useEffect(() => {
    if (isAuthenticated) {
      getKnowledgeBases();
    }
  }, [isAuthenticated, getKnowledgeBases]);

  const onMenuClick = useCallback(
    (slug: string) => {
      setOpenPopover(false);

      if (kbSlugValue !== slug) {
        router.push(`/knowledge-bases/${slug}/`);
      }
    },
    [kbSlugValue, router],
  );

  const items = useMemo(() => {
    if (search) {
      return data
        .filter((space) => !!space.slug)
        .filter((space) =>
          (space.name || '').toLowerCase().includes(search.toLowerCase()),
        )
        .map((space) => ({
          label: space.name || '',
          key: space.slug || '',
          icon: getPostIcon(space.type || ''),
          rightIcon: space.content_type !== 'general' && (
            <StyledLabel>{space.content_type}</StyledLabel>
          ),
          onClick: () => space.slug && onMenuClick(space.slug),
        }));
    }

    return data
      .filter((space) => !!space.slug)
      .map((space) => ({
        label: space.name || '',
        key: space.slug || '',
        icon: getPostIcon(space.privacy_type || ''),
        rightIcon: space.content_type !== 'general' && (
          <StyledLabel>{space.content_type}</StyledLabel>
        ),
        onClick: () => space.slug && onMenuClick(space.slug),
      }));
  }, [data, search, onMenuClick]);

  const onCreateClick = () => {
    setOpenPopover(false);
    setAddNew(true);
  };

  const onCreated = (response: any) => {
    getKnowledgeBases();
    router.push(`/knowledge-bases/${response.data.slug}`);
  };

  const breadcrumbItems = [
    {
      title: (
        <AppLink href={`/knowledge-bases/`}>
          {formatMessage({id: 'common.home'})}
        </AppLink>
      ),
    },
    {
      title: <AppBreadCrumbTitle title={currentKb?.name || pageTitle}/>,
    },
  ];

  const document = getStatusOptionsFromConfig(
    COLLECTION_TYPE_DATA as any,
    formatMessage,
  ).find((item: any) => item.id === currentKb?.content_type);

  return (
    <Fragment>
      <StyledTitleBlock>
        <StyledIconWrapper>
          <BsDatabase size={21}/>
        </StyledIconWrapper>
        <StyledTitleWrapper>
          <AppPopover
            open={openPopover}
            content={
              <StyledMenusContainer>
                <StyledInputWrapper>
                  <StyledInput
                    placeholder={formatMessage({id: 'common.searchHere'})}
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />

                  <Tooltip title={formatMessage({id: 'common.refresh'})}>
                    <Button
                      type="text"
                      size="small"
                      icon={<MdRefresh fontSize={24}/>}
                      onClick={() => getKnowledgeBases()}
                      loading={loading}
                    />
                  </Tooltip>
                </StyledInputWrapper>

                <AppCustomMenus
                  items={items}
                  activeKeys={kbSlugValue ? [kbSlugValue] : []}
                />

                {loading && (
                  <StyledLoader>
                    <AppLoader
                      position="relative"
                      style={{backgroundColor: 'transparent'}}
                    />
                  </StyledLoader>
                )}

                <StyledAddButton onClick={() => onCreateClick()}>
                  <MdAddCircleOutline fontSize={16}/>
                  <span>
                    {formatMessage({id: 'knowledgeBase.addKnowledgeBase'})}
                  </span>
                </StyledAddButton>
              </StyledMenusContainer>
            }
            style={{zIndex: 1000}}
            onOpenChange={setOpenPopover}
          >
            <StyledTitleContent>
              <StyledMainTitle ellipsis={{rows: 1}}>
                {currentKb?.name || pageTitle}
              </StyledMainTitle>
              {document && (
                <StyledLabel color={theme.palette.primary}>
                  {formatMessage({id: document?.name}) ||
                    formatMessage({id: 'space.general'})}
                </StyledLabel>
              )}

              <StyledDropdownArrow>
                <MdOutlineArrowDropUp fontSize={18}/>
                <MdOutlineArrowDropDown fontSize={18}/>
              </StyledDropdownArrow>
            </StyledTitleContent>
          </AppPopover>

          {currentKb?.name && <AppBreadCrumb items={breadcrumbItems}/>}
        </StyledTitleWrapper>
      </StyledTitleBlock>

      <AppNewKb addNew={addNew} setAddNew={setAddNew} onCreated={onCreated}/>
    </Fragment>
  );
};

export default HeaderDropdown;
