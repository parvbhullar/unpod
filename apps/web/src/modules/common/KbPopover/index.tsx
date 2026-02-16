import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import { Badge, Tooltip } from 'antd';
import { isArray } from 'lodash';
import { MdCheckBox, MdCheckBoxOutlineBlank } from 'react-icons/md';
import { BsDatabase } from 'react-icons/bs';
import clsx from 'clsx';
import { getPostIcon } from '@unpod/helpers/PermissionHelper';
import { useAuthContext, useGetDataApi } from '@unpod/providers';
import {
  StyledIconButton,
  StyledInputWrapper,
  StyledKbActions,
  StyledKbMenus,
  StyledMenus,
  StyledSearchInput,
} from './index.styled';
import { AppPopover } from '@unpod/components/antd';
import type { AppCustomMenuItem, Spaces } from '@unpod/constants/types';

type KbPopoverProps = {
  knowledgeBases: string[];
  setKnowledgeBases: React.Dispatch<React.SetStateAction<string[]>>;
};

const KbPopover: React.FC<KbPopoverProps> = ({
  knowledgeBases,
  setKnowledgeBases,
}) => {
  const { formatMessage } = useIntl();
  const { isAuthenticated } = useAuthContext();
  const [search, setSearch] = useState('');

  const [{ apiData }, { reCallAPI }] = useGetDataApi<Spaces[]>(
    `core/knowledgebase/`,
    { data: [] },
    {},
    false,
  );

  useEffect(() => {
    if (isAuthenticated) {
      reCallAPI();
    }
  }, [isAuthenticated]);

  const onKbSelect = useCallback(
    (item: Spaces) => {
      const slug = item.slug;
      if (!slug) return;
      if (!knowledgeBases.includes(slug)) {
        setKnowledgeBases((prevState) => [...prevState, slug]);
      } else {
        setKnowledgeBases((prevState) => prevState.filter((kb) => kb !== slug));
      }
    },
    [knowledgeBases],
  );

  const kbItems = useMemo<AppCustomMenuItem[]>(() => {
    if (apiData?.data && isArray(apiData.data)) {
      const filtered = search
        ? apiData.data.filter((item) =>
            (item.name || '').toLowerCase().includes(search.toLowerCase()),
          )
        : apiData.data;

      return filtered
        .filter((item) => Boolean(item.slug))
        .map((item) => ({
          key: item.slug as string,
          label: item.name || item.slug,
          icon: getPostIcon(String(item.privacy_type || 'public')),
          onClick: () => onKbSelect(item),
        }));
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
      setKnowledgeBases(kbItems.map((item) => item.key));
    }
  };

  return (
    <AppPopover
      content={
        <StyledKbMenus>
          <StyledInputWrapper>
            <StyledSearchInput
              placeholder={formatMessage({ id: 'common.searchHere' })}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </StyledInputWrapper>
          <StyledMenus
            items={kbItems}
            activeKeys={knowledgeBases}
            showCheckIcon
          />

          <StyledKbActions
            className={clsx({ 'all-selected': allSelected })}
            onClick={toggleSelectAll}
          >
            {allSelected ? (
              <MdCheckBox fontSize={18} />
            ) : (
              <MdCheckBoxOutlineBlank fontSize={18} />
            )}
            {allSelected
              ? formatMessage({ id: 'common.unselectAll' })
              : formatMessage({ id: 'common.selectAll' })}
          </StyledKbActions>
        </StyledKbMenus>
      }
      arrow
    >
      <Badge count={knowledgeBases?.length} offset={[-5, 2]}>
        <Tooltip title={formatMessage({ id: 'nav.knowledgeBase' })}>
          <StyledIconButton type="text" shape="round">
            <BsDatabase fontSize={18} />
          </StyledIconButton>
        </Tooltip>
      </Badge>
    </AppPopover>
  );
};

export default KbPopover;
