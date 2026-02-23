import {useAppActionsContext, useAppContext} from '@unpod/providers';
import {MenuFoldOutlined, MenuUnfoldOutlined} from '@ant-design/icons';

const AppToggleSidebar = () => {
  const {collapsed} = useAppContext();
  const {setCollapsed} = useAppActionsContext();

  return collapsed ? (
    <MenuUnfoldOutlined
      className="trigger"
      onClick={() => setCollapsed(!collapsed)}
    />
  ) : (
    <MenuFoldOutlined
      className="trigger"
      onClick={() => setCollapsed(!collapsed)}
    />
  );
};

export default AppToggleSidebar;
