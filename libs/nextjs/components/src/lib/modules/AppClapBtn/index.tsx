import {useCallback, useState} from 'react';
import {Tooltip, Typography} from 'antd';
import {AppClapsIcon} from '@unpod/icons';
import _ from 'lodash';

import styled from 'styled-components';
import {GlobalTheme} from '@unpod/constants';

const StyledItemWrapper = styled.div`
  cursor: pointer;
  user-select: none;
  display: flex;
  gap: 8px;

  &:hover .ant-typography {
    color: ${({theme}: { theme: GlobalTheme }) => theme.palette.primary};
  }
`;

type AppClapBtnProps = {
  clapCount?: number;
  onClapClick?: (count: number) => void;
};

const AppClapBtn = ({clapCount, onClapClick}: AppClapBtnProps) => {
  const [userClapCount, setUserClapCount] = useState(0);

  const debounceClapClick = useCallback(
    _.debounce((reactionCount: number) => {
      setUserClapCount(0);
      if (onClapClick) onClapClick(reactionCount);
    }, 500),
    [onClapClick],
  );

  return (
    <Tooltip
      placement="top"
      title={userClapCount}
      styles={{
        container: {
          textAlign: 'center',
        },
      }}
      open={userClapCount > 0}
    >
      <StyledItemWrapper
        onClick={(e) => {
          e.stopPropagation();
          setUserClapCount(userClapCount + 1);
          debounceClapClick(userClapCount + 1);
        }}
      >
        <Typography.Text type="secondary">
          <span style={{display: 'inline-flex', fontSize: 24}}>
            <AppClapsIcon/>
          </span>
        </Typography.Text>
        <Typography.Text>{clapCount}</Typography.Text>
      </StyledItemWrapper>
    </Tooltip>
  );
};

export default AppClapBtn;

