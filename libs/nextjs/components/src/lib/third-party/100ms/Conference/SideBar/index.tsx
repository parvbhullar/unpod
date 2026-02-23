import React from 'react';
import {StyledRoot} from './index.styled';
import PostDetails from './PostDetails';

const SideBar = () => {
  return (
    <StyledRoot>
      <PostDetails/>
    </StyledRoot>
  );
};

export default React.memo(SideBar);
