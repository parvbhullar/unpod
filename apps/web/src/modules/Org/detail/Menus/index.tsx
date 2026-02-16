import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import PageSidebar from '@unpod/components/common/AppPageLayout/layouts/ThreeColumnPageLayout/PageSidebar';
import { BiBot } from 'react-icons/bi';
import { StyledAvatar, StyledIconWrapper } from './index.styled';
import type { Pilot } from '@unpod/constants/types';

type MenuItem = {
  label: React.ReactNode;
  key: string;
  icon?: React.ReactNode;
  title?: string;
};

const getItem = (options: MenuItem) => {
  const { label, key, icon, title } = options;

  return {
    key: key,
    icon,
    label,
    title,
  };
};

type MenusProps = {
  onPilotClick: (pilot: Pilot | 'superpilot') => void;
};

const Menus: React.FC<MenusProps> = ({ onPilotClick }) => {
  const infoViewActionsContext = useInfoViewActionsContext();

  const [pilots, setPilots] = useState<Pilot[]>([]);
  const [activeKey, setActiveKey] = useState('superpilot');
  const [loading, setLoading] = useState(true);

  const getPilots = useCallback(() => {
    setLoading(true);
    getDataApi<Pilot[]>(`core/pilots/`, infoViewActionsContext, {
      case: 'home',
    })
      .then((response) => {
        setPilots(response.data || []);
        setLoading(false);
      })
      .catch((error) => {
        const err = error as { message?: string };
        setLoading(false);
        infoViewActionsContext.showError(err.message || 'Error');
      });
  }, [infoViewActionsContext]);

  useEffect(() => {
    getPilots();
  }, []);

  const items = useMemo(() => {
    return [
      {
        label: '@Superpilot',
        key: 'superpilot',
        icon: (
          <StyledIconWrapper>
            <BiBot fontSize={20} />
          </StyledIconWrapper>
        ),
      },
      ...pilots.map((pilot) => {
        return getItem({
          label: pilot.name || '',
          key: pilot.handle || '',
          icon: pilot?.logo ? (
            <StyledAvatar
              shape="square"
              src={`${pilot.logo}?tr=w-100,h-100`}
              size={32}
            />
          ) : (
            <StyledIconWrapper>
              <BiBot fontSize={20} />
            </StyledIconWrapper>
          ),
        });
      }),
    ];
  }, [pilots]);

  const onMenuClick = (option: { key: string }) => {
    setActiveKey(option.key);
    onPilotClick(
      option.key === 'superpilot'
        ? 'superpilot'
        : pilots.find((pilot) => pilot.handle === option.key) || 'superpilot',
    );
  };

  return (
    <PageSidebar
      defaultSelectedKeys={[activeKey]}
      selectedKeys={[activeKey]}
      defaultOpenKeys={[activeKey]}
      items={items as any}
      onMenuClick={onMenuClick}
      loading={loading}
    />
  );
};

export default React.memo(Menus);
