import React, { ReactNode } from 'react';
import styled from 'styled-components';

const StyledPlaygroundTile = styled.div<{
  $padding?: boolean;
  $backgroundColor?: string;
  $title?: string;
}>`
  display: flex;
  flex-direction: column;
  border: 1px solid #999999;
  border-radius: 4px;
  background-color: ${({ $backgroundColor }) =>
    $backgroundColor || 'transparent'};
  color: #6b7280;
  & .title {
    display: flex;
    align-items: center;
    justify-content: center;
    text-transform: uppercase;
    font-size: 0.75rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #999999;
    height: 32px;
    letter-spacing: 0.05em;
  }
  & .content {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex-grow: 1;
    width: 100%;
    padding: ${({ $padding }) => ($padding ? '16px' : '0')};
    height: ${({ $title }) => ($title ? 'calc(100% - 32px)' : '100%')};
  }
`;

export type PlaygroundTileProps = {
  children?: ReactNode;
  title?: string;
  className?: string;
  childrenClassName?: string;
  padding?: boolean;
  backgroundColor?: string;};

export const PlaygroundTile: React.FC<PlaygroundTileProps> = ({
  children,
  title,
  className,
  childrenClassName,
  padding = true,
  backgroundColor = 'transparent',
}) => {
  return (
    <StyledPlaygroundTile
      className={className}
      $padding={padding}
      $backgroundColor={backgroundColor}
      $title={title}
    >
      {title && (
        <div className="title">
          <h2>{title}</h2>
        </div>
      )}
      <div className={`content ${childrenClassName}`}>{children}</div>
    </StyledPlaygroundTile>
  );
};
