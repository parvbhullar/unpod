import type { ChangeEvent, ReactNode } from 'react';
import { useMemo } from 'react';

import { BiBot } from 'react-icons/bi';
import { useGetDataApi } from '@unpod/providers';
import { debounce, isArray } from 'lodash';
import {
  StyledButton,
  StyledInputWrapper,
  StyledKbMenus,
  StyledMenus,
  StyledSearchInput,
} from './index.styled';
import { AppPopover } from '../../antd';
import { useIntl } from 'react-intl';

type AgentPilot = {
  handle?: string;
  name?: string;
  [key: string]: any;
};

type AppAgentPopoverProps = {
  pilot?: AgentPilot | null;
  setPilot: (pilot: AgentPilot | null) => void;
  type?: string;
  renderChildren?: (pilot?: AgentPilot | null) => ReactNode;};

const AppAgentPopover = ({
  pilot,
  setPilot,
  type,
  renderChildren,
}: AppAgentPopoverProps) => {
  const { formatMessage } = useIntl();
  const [{ apiData }, { setQueryParams }] = useGetDataApi(
    `core/pilots/org/`,
    { data: [] },
    { type, search: pilot?.name || '' },
    true,
    ({ data }: { data: AgentPilot[] }) => {
      if (!pilot?.handle) {
        setPilot(
          data.find((item: AgentPilot) => item.handle === pilot?.name) || null,
        );
      }
    },
  );

  const items = useMemo(() => {
    const onItemClick = (item: AgentPilot) => {
      setPilot(item);
    };

    if (apiData?.data && isArray(apiData.data)) {
      return [...apiData.data].map((item: AgentPilot, index: number) => {
        const itemKey = item.handle || item.slug || item.name || String(index);
        return {
          key: itemKey,
          label: item.name,
          icon: <BiBot fontSize={18} />,
          onClick: () => onItemClick(item),
        };
      });
    }
    return [];
  }, [apiData, setPilot]);

  const onSearch = (value: string) => {
    setQueryParams({ search: value, type: 'Voice' });
  };

  return (
    <AppPopover
      content={
        <StyledKbMenus>
          <StyledInputWrapper>
            <StyledSearchInput
              placeholder={formatMessage({ id: 'agent.searchAgents' })}
              onChange={
                debounce(
                  (event: ChangeEvent<HTMLInputElement>) =>
                    onSearch(event.target.value),
                  300,
                ) as unknown as (event: ChangeEvent<HTMLInputElement>) => void
              }
              defaultValue={pilot?.name || ''}
              allowClear
            />
          </StyledInputWrapper>
          <StyledMenus
            items={items}
            activeKeys={pilot?.handle ? [pilot.handle] : []}
            showCheckIcon
          />
        </StyledKbMenus>
      }
    >
      {renderChildren ? (
        renderChildren(pilot)
      ) : (
        <StyledButton type="default" shape="round">
          <BiBot fontSize={18} />
          {pilot?.name ||
            formatMessage({ id: 'appSpaceCallModal.selectAgent' })}
        </StyledButton>
      )}
    </AppPopover>
  );
};

export default AppAgentPopover;
