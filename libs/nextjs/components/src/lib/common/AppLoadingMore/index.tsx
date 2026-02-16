import styled from 'styled-components';
import { Spin } from 'antd';

const StyledLoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 14px;
  background: #eae6ff;
  border-radius: 24px;
  transition: background 0.3s;
`;

const StyledLoadingRoot = styled.div`
  display: flex;
  justify-content: center;
  position: absolute;
  top: auto;
  bottom: 40px;
  right: 0;
  left: 0;
  z-index: 999900009;

  &:hover ${StyledLoadingContainer} {
    background: #d8d1ff;
  }
`;

const AppLoadingMore = () => {
  return (
    <StyledLoadingRoot role="progress-loader">
      <StyledLoadingContainer>
        <span role="spin">
          <Spin />
        </span>
        Loading more...
      </StyledLoadingContainer>
    </StyledLoadingRoot>
  );
};

export default AppLoadingMore;
