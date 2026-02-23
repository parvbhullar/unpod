import React, {ReactNode} from 'react';
import {StyledActionContainer, StyledHeader, StyledRoot, StyledStickyContainer, StyledTitle,} from './index.styled';
import SearchBox from './SearchBox';
import AppMenu from '../../antd/AppMenu';
import AppLoadingMore from '../AppLoadingMore';
import {Button, Divider, Typography} from 'antd';
import {MdAdd, MdOutlinePhone} from 'react-icons/md';
import {MenuProps} from 'antd/es/menu';

const {Title} = Typography;

type AppSidebarProps = {
  title?: string;
  items?: MenuProps['items'];
  loading?: boolean;
  initialLoader?: ReactNode;
  noDataMessage?: string;
  selectedKeys?: string[];
  onSelectMenu?: MenuProps['onSelect'];
  onEndReached?: () => void;
  onClickAdd?: () => void;
  onSearch?: (value: string) => void;
  isLoadingMore?: boolean;
};

const AppSidebar: React.FC<AppSidebarProps> = ({
                                                 title,
                                                 items,
                                                 loading,
                                                 initialLoader,
                                                 noDataMessage = 'No records found',
                                                 selectedKeys,
                                                 onSelectMenu,
                                                 onEndReached,
                                                 onClickAdd,
                                                 onSearch,
                                                 isLoadingMore,
                                               }) => {
  return (
    <StyledRoot>
      <StyledStickyContainer>
        <StyledHeader>
          <StyledTitle>
            <MdOutlinePhone fontSize={21}/>
            <Title level={4} style={{margin: 0}}>
              {title}
            </Title>
          </StyledTitle>

          {onClickAdd ? (
            <Button
              type="primary"
              shape="circle"
              size="small"
              onClick={onClickAdd}
              icon={<MdAdd fontSize={18}/>}
            />
          ) : null}
        </StyledHeader>

        <Divider style={{margin: 0}}/>

        {onSearch ? (
          <StyledActionContainer>
            <SearchBox onSearch={onSearch}/>
          </StyledActionContainer>
        ) : null}
      </StyledStickyContainer>
      <AppMenu
        items={items}
        loading={loading}
        initialLoader={initialLoader}
        noDataMessage={noDataMessage}
        selectedKeys={selectedKeys}
        onSelect={onSelectMenu}
        onEndReached={onEndReached}
      />
      {isLoadingMore && <AppLoadingMore/>}
    </StyledRoot>
  );
};

export default AppSidebar;
