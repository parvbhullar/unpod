import type {ChangeEvent} from 'react';
import {useMemo} from 'react';

import {Tooltip} from 'antd';
import {MdInfoOutline} from 'react-icons/md';
import {BiBot} from 'react-icons/bi';
import {useGetDataApi} from '@unpod/providers';
import {debounce, isArray} from 'lodash';
import {StyledButton, StyledInputWrapper, StyledKbMenus, StyledMenus, StyledSearchInput,} from './index.styled';
import {AppPopover} from '../../antd';
import {useIntl} from 'react-intl';
import {getLocalizedOptions} from '@unpod/helpers/LocalizationFormatHelper';

/*export const defaultPilot = {
  slug: 'multi-ai',
  name: '@Superpilot',
  logo: null,
};*/

const focusData = [
  {
    key: 'my_space',
    label: 'pilot.mySpace',
    icon: <BiBot fontSize={18}/>,
    rightIcon: (
      <Tooltip title="pilot.mySpaceInfo">
        <MdInfoOutline fontSize={18}/>
      </Tooltip>
    ),
  },
  {
    key: 'public',
    label: 'pilot.public',
    icon: <BiBot fontSize={18}/>,
    rightIcon: (
      <Tooltip title="pilot.publicInfo">
        <MdInfoOutline fontSize={18}/>
      </Tooltip>
    ),
  },
  {
    key: 'my_agents',
    label: 'pilot.myAgents',
    icon: <BiBot fontSize={18}/>,
    rightIcon: (
      <Tooltip title="pilot.myAgentsInfo">
        <MdInfoOutline fontSize={18}/>
      </Tooltip>
    ),
  },
];

type PilotItem = {
  handle?: string;
  name?: string;
  slug?: string;
  [key: string]: any;
};

type AppPilotPopoverProps = {
  pilot?: PilotItem | null;
  setPilot: (pilot: PilotItem | null) => void;
  focus?: string;
  setFocus: (focus: string) => void;
  isMySpace?: boolean;
};

const AppPilotPopover = ({
                           pilot,
                           setPilot,
                           focus,
                           setFocus,
                           isMySpace,
                         }: AppPilotPopoverProps) => {
  const {formatMessage} = useIntl();
  const [{apiData}, {setQueryParams}] = useGetDataApi(
    `core/pilots/org/`,
    {data: []},
    {},
  );

  const focusItems = useMemo(() => {
    const onItemClick = (key: string) => {
      setFocus(key);
      setPilot(null);
    };

    if (isMySpace) {
      return focusData
        .filter((item) => item.key !== 'public')
        .map((item) => {
          return {
            ...item,
            onClick: () => onItemClick(item.key),
          };
        });
    }

    return focusData
      .filter((item) => item.key !== 'my_space')
      .map((item) => {
        return {
          ...item,
          onClick: () => onItemClick(item.key),
        };
      });
  }, [setFocus, setPilot, isMySpace]);

  const items = useMemo(() => {
    const onItemClick = (item: PilotItem) => {
      setFocus('selected_agent');
      setPilot(item);
    };

    if (apiData?.data && isArray(apiData.data)) {
      /*if (search) {
        return [...apiData.data]
          .filter((item) =>
            item.name.toLowerCase().includes(search.toLowerCase())
          )
          .map((item) => {
            return {
              key: item.slug,
              label: item.name,
              icon: <BiBot fontSize={18} />,
              onClick: () => onItemClick(item),
            };
          });
      }*/

      return [...apiData.data].map((item: PilotItem, index: number) => {
        const itemKey = item.handle || item.slug || item.name || String(index);
        return {
          key: itemKey,
          label: item.name,
          icon: <BiBot fontSize={18}/>,
          onClick: () => onItemClick(item),
        };
      });
    }
    return [];
  }, [apiData, setPilot, setFocus]);

  const onSearch = (value: string) => {
    setQueryParams({search: value});
  };

  const focusItem = focusData.find((item) => item.key === focus);

  return (
    process.env.isDevMode === 'yes' && (
      <AppPopover
        content={
          <StyledKbMenus>
            <StyledMenus
              items={getLocalizedOptions(focusItems, formatMessage) as any}
              activeKeys={focus ? [focus] : []}
              showCheckIcon
            />
            <StyledInputWrapper>
              <StyledSearchInput
                placeholder={formatMessage({id: 'agent.searchAgents'})}
                onChange={
                  debounce(
                    (event: ChangeEvent<HTMLInputElement>) =>
                      onSearch(event.target.value),
                    300,
                  ) as unknown as (event: ChangeEvent<HTMLInputElement>) => void
                }
              />
            </StyledInputWrapper>
            <StyledMenus
              items={items}
              activeKeys={pilot?.handle ? [pilot.handle] : []}
              showCheckIcon
            />
          </StyledKbMenus>
        }
        arrow
      >
        {pilot ? (
          <StyledButton type="default" shape="round">
            <BiBot fontSize={18}/>
            {pilot.name}
          </StyledButton>
        ) : (
          <StyledButton type="default" shape="round">
            {focusItem?.icon || <BiBot fontSize={18}/>}
            {formatMessage({id: focusItem?.label}) ||
              formatMessage({id: 'appSpaceCallModal.selectAgent'})}
          </StyledButton>
        )}
      </AppPopover>
    )
  );
};

export default AppPilotPopover;
