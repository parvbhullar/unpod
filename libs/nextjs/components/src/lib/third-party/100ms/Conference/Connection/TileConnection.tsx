import React from 'react';
import { ConnectionIndicator } from './ConnectionIndicator';
import styled from 'styled-components';
import { Typography } from 'antd';

const TileConnection = ({ name, peerId, hideLabel, isMouseHovered }) => {
  return (
    <StyledWrapper $isMouseHovered={isMouseHovered}>
      {!hideLabel ? (
        <Typography.Paragraph ellipsis={true}>{name}</Typography.Paragraph>
      ) : null}
      <ConnectionIndicator isTile peerId={peerId} />
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  position: absolute;
  bottom: 8px;
  left: 8px;
  color: white;
  background-color: #45454533;
  border-radius: 8px;
  z-index: 1;
  padding: 3px 8px;
  max-width: calc(100% - 16px);
  opacity: ${({ $isMouseHovered }) => ($isMouseHovered ? 1 : 0.8)};
  transition: opacity 0.2s ease-in;

  & .ant-typography {
    color: white !important;
    margin-bottom: 0;
    font-size: 0.75rem;
  }

,
`;

export default TileConnection;
