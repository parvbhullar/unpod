import {StyledRoot, StyledRootWrapper} from './index.styled';

const ContentWrapper = ({children}: { children?: any }) => {
  return (
    <StyledRootWrapper>
      <StyledRoot>{children}</StyledRoot>
    </StyledRootWrapper>
  );
};

export default ContentWrapper;
