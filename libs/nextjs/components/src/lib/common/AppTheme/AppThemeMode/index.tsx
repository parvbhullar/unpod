import React, {type ReactNode} from 'react';
import {useAppActionsContext, useAppContext} from '@unpod/providers';
import {Switch} from 'antd';
import styled from 'styled-components';

const AppThemeMode = () => {
  const {themeMode} = useAppContext(); // This would typically come from props or context
  const {updateThemeMode} = useAppActionsContext(); // This would typically come from props or context

  // graceful fallbacks if antd or styled-components aren't imported yet
  type SwitchFallbackProps = {
    checked?: boolean;
    onChange?: (checked: boolean) => void;
  };

  type ContainerProps = {
    children?: ReactNode;
  };

  const AntSwitch =
    typeof Switch !== 'undefined'
      ? Switch
      : ({checked, onChange}: SwitchFallbackProps) => (
        <input
          type="checkbox"
          checked={!!checked}
          onChange={(e) => onChange && onChange(e.target.checked)}
          aria-label="theme-switch"
        />
      );

  const Container =
    typeof styled !== 'undefined'
      ? styled.div`
          display: flex;
          align-items: center;
          gap: 8px;
        `
      : ({
           children,
           ...rest
         }: ContainerProps & React.HTMLAttributes<HTMLDivElement>) =>
        React.createElement(
          'div',
          {
            ...rest,
            style: {display: 'flex', alignItems: 'center', gap: 8},
          },
          children,
        );

  return (
    <Container>
      <AntSwitch
        checkedChildren="🌙"
        unCheckedChildren="☀️"
        checked={themeMode === 'dark'}
        onChange={(checked) => updateThemeMode(checked ? 'dark' : 'light')}
      />
    </Container>
  );
};

export default AppThemeMode;
