import React, {ReactNode, useEffect, useRef} from 'react';
import type {SegmentedProps} from 'antd';
import {Button, Divider, Dropdown} from 'antd';
import {MoreOutlined} from '@ant-design/icons';
import {
  StyledMobileTabsContent,
  StyledScrollArea,
  StyledSegmented,
  StyledTabsContent,
  StyledWrapper,
} from './index.styled';
import {useMediaQuery} from 'react-responsive';
import {MobileWidthQuery} from '@unpod/constants';

type SegmentedTab = {
  value: string | number;
  label: ReactNode;
  icon?: ReactNode;
};

type AppSegmentedProps = {
  value?: string | number;
  onChange: (value: string | number) => void;
  tabs: SegmentedTab[];
  divider?: boolean;
  CenterSegmented?: boolean;
};

const AppSegmented: React.FC<AppSegmentedProps> = ({
                                                     value,
                                                     onChange,
                                                     tabs,
                                                     divider = true,
                                                     CenterSegmented = true,
                                                   }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mobileScreen = useMediaQuery(MobileWidthQuery);

  useEffect(() => {
    const active = containerRef.current?.querySelector(
      '.ant-segmented-item-selected',
    );
    if (active) {
      active.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'nearest',
      });
    }
  }, [value]);

  return (
    <>
      <StyledWrapper>
        <StyledScrollArea
          ref={containerRef}
          className={CenterSegmented ? 'CenterSegmented' : undefined}
        >
          {(() => {
            const handleChange: SegmentedProps['onChange'] = (val) =>
              onChange(val as string | number);
            return (
              <StyledSegmented
                value={value}
                onChange={handleChange}
                options={tabs.map((tab) => ({
                  value: tab.value,
                  label: (
                    <StyledTabsContent>
                      {tab.icon}
                      {tab.label}
                    </StyledTabsContent>
                  ),
                }))}
              />
            );
          })()}
        </StyledScrollArea>

        {mobileScreen && tabs.length > 0 && (
          <Dropdown
            menu={{
              items: tabs.map((t) => ({
                key: t.value,
                label: (
                  <StyledMobileTabsContent onClick={() => onChange(t.value)}>
                    {t.icon}
                    {t.label}
                  </StyledMobileTabsContent>
                ),
              })),
            }}
            trigger={['click']}
          >
            <Button icon={<MoreOutlined/>} type="text"/>
          </Dropdown>
        )}
      </StyledWrapper>
      {divider && <Divider style={{margin: 0}}/>}
    </>
  );
};

export default AppSegmented;
