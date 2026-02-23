import type {ChangeEvent, Dispatch, ReactNode, SetStateAction} from 'react';
import {useCallback, useEffect, useMemo, useState} from 'react';

import {Badge, Tooltip} from 'antd';
import {isArray} from 'lodash';
import {MdCheckBox, MdCheckBoxOutlineBlank} from 'react-icons/md';
import {BsDatabase} from 'react-icons/bs';
import clsx from 'clsx';
import {getPostIcon} from '@unpod/helpers/PermissionHelper';
import {useAuthContext, useGetDataApi} from '@unpod/providers';
import {
  StyledIconButton,
  StyledInputWrapper,
  StyledKbActions,
  StyledKbMenus,
  StyledMenus,
  StyledSearchInput,
} from './index.styled';
import {AppPopover} from '../../antd';
import {useIntl} from 'react-intl';

type KnowledgeBaseItem = {
  slug: string;
  name: string;
  privacy_type?: string;
};

type KbMenuItem = {
  key: string;
  label: string;
  icon?: ReactNode;
  onClick: () => void;
};

type AppKbPopoverProps = {
  knowledgeBases: string[];
  setKnowledgeBases: Dispatch<SetStateAction<string[]>>;
};

const AppKbPopover = ({
                        knowledgeBases,
                        setKnowledgeBases,
                      }: AppKbPopoverProps) => {
  const {isAuthenticated} = useAuthContext();
  const [search, setSearch] = useState('');
  const {formatMessage} = useIntl();

  const [{apiData}, {reCallAPI}] = useGetDataApi(
    `core/knowledgebase/`,
    {data: []},
    {},
    false,
  );

  useEffect(() => {
    if (isAuthenticated) {
      reCallAPI();
    }
  }, [isAuthenticated]);

  const onKbSelect = useCallback(
    (item: KnowledgeBaseItem) => {
      if (!knowledgeBases.includes(item.slug)) {
        setKnowledgeBases((prevState) => [...prevState, item.slug]);
      } else {
        setKnowledgeBases((prevState) =>
          prevState.filter((kb) => kb !== item.slug),
        );
      }
    },
    [knowledgeBases],
  );

  const kbItems = useMemo(() => {
    if (apiData?.data && isArray(apiData.data)) {
      if (search) {
        return apiData.data
          .filter((item: KnowledgeBaseItem) =>
            (item.name || '').toLowerCase().includes(search.toLowerCase()),
          )
          .map((item: KnowledgeBaseItem): KbMenuItem => {
            return {
              key: item.slug,
              label: item.name,
              icon: getPostIcon(item.privacy_type || ''),
              onClick: () => onKbSelect(item),
            };
          });
      }

      return apiData.data.map((item: KnowledgeBaseItem): KbMenuItem => {
        return {
          key: item.slug,
          label: item.name,
          icon: getPostIcon(item.privacy_type || ''),
          onClick: () => onKbSelect(item),
        };
      });
    }
    return [];
  }, [apiData, search, onKbSelect]);

  const allSelected = useMemo(() => {
    return kbItems.length === knowledgeBases.length;
  }, [kbItems, knowledgeBases]);

  const toggleSelectAll = () => {
    if (allSelected) {
      setKnowledgeBases([]);
    } else {
      setKnowledgeBases(kbItems.map((item: KbMenuItem) => item.key));
    }
  };

  return (
    <AppPopover
      content={
        <StyledKbMenus>
          <StyledInputWrapper>
            <StyledSearchInput
              placeholder={formatMessage({id: 'common.searchHere'})}
              value={search}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                setSearch(event.target.value)
              }
            />
          </StyledInputWrapper>
          <StyledMenus
            items={kbItems}
            activeKeys={knowledgeBases}
            showCheckIcon
          />

          <StyledKbActions
            className={clsx({'all-selected': allSelected})}
            onClick={toggleSelectAll}
          >
            {allSelected ? (
              <MdCheckBox fontSize={18}/>
            ) : (
              <MdCheckBoxOutlineBlank fontSize={18}/>
            )}
            {allSelected
              ? formatMessage({id: 'common.unselectAll'})
              : formatMessage({id: 'common.selectAll'})}
          </StyledKbActions>
        </StyledKbMenus>
      }
      arrow
    >
      <Badge count={knowledgeBases?.length} offset={[-5, 2]}>
        <Tooltip title={formatMessage({id: 'knowledgeBase.pageTitle'})}>
          <StyledIconButton type="text" shape="round">
            <BsDatabase fontSize={18}/>
          </StyledIconButton>
        </Tooltip>
      </Badge>
    </AppPopover>
  );
};

export default AppKbPopover;
