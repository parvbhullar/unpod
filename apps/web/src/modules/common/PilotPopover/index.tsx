import React, { useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import { BiBot } from 'react-icons/bi';
import {
  StyledButton,
  StyledInputWrapper,
  StyledKbMenus,
  StyledMenus,
  StyledSearchInput,
} from './index.styled';
import { useGetDataApi } from '@unpod/providers';
import { isArray } from 'lodash';
import { AppPopover } from '@unpod/components/antd';
import type { AppCustomMenuItem, Pilot } from '@unpod/constants/types';

export const defaultPilot = {
  slug: 'multi-ai',
  name: 'Multi-AI',
  logo: null,
};

type PilotPopoverProps = {
  pilot: Pilot | null;
  setPilot: React.Dispatch<React.SetStateAction<Pilot | null>>;
};

const PilotPopover: React.FC<PilotPopoverProps> = ({ pilot, setPilot }) => {
  const { formatMessage } = useIntl();
  const [search, setSearch] = useState('');

  const [{ apiData }] = useGetDataApi<Pilot[]>(
    `core/pilots/public/`,
    { data: [] },
    {},
  );

  const items = useMemo<AppCustomMenuItem[]>(() => {
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
          icon: <BiBot fontSize={18} />,
          onClick: () => setPilot(item),
        }));
    }
    return [];
  }, [apiData, search, setPilot]);

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
            items={items}
            activeKeys={
              pilot ? [pilot.handle || pilot.slug || ''].filter(Boolean) : []
            }
            showCheckIcon
          />
        </StyledKbMenus>
      }
      arrow
    >
      <StyledButton type="default" shape="round">
        <BiBot fontSize={18} />
        {pilot ? pilot.name : 'Multi-AI'}
      </StyledButton>
    </AppPopover>
  );
};

export default PilotPopover;
