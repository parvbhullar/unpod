import React, {ReactNode} from 'react';
import {Panel, PanelGroup} from 'react-resizable-panels';
import {useMediaQuery} from 'react-responsive';
import {StyledPanelResizeHandle, StyledRoot} from './index.styled';
import {TabWidthQuery} from '@unpod/constants';

type AppSplitPaneProps = {
  children: ReactNode;
  sidebar?: ReactNode;
  rightSidebar?: ReactNode;
  allowResize?: boolean;
};

const AppSplitPane: React.FC<AppSplitPaneProps> = ({
                                                     children,
                                                     sidebar = null,
                                                     rightSidebar,
                                                     allowResize = true,
                                                     ...restProps
                                                   }) => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);

  return (
    <StyledRoot>
      {isTabletOrMobile ? (
        children
      ) : (
        <PanelGroup direction="horizontal">
          <Panel defaultSize={30} minSize={25} {...restProps}>
            {sidebar}
          </Panel>

          <StyledPanelResizeHandle disabled={!allowResize}/>

          <Panel minSize={50}>{children}</Panel>

          {rightSidebar && (
            <>
              <StyledPanelResizeHandle disabled={!allowResize}/>
              <Panel defaultSize={30} minSize={25}>
                {rightSidebar}
              </Panel>
            </>
          )}
        </PanelGroup>
      )}
    </StyledRoot>
  );
};

export default AppSplitPane;
