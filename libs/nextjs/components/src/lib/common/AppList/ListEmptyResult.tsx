import React, {MouseEventHandler, ReactNode} from 'react';
import {Button, Spin} from 'antd';
import {StyledEmptyListContainer, StyledEmptyListContainerFlex,} from './index.styled';

type ListEmptyResultProps = {
  loading?: boolean;
  title?: ReactNode;
  actionTitle?: string;
  noDataMessage?: string;
  onClick?: MouseEventHandler<HTMLElement>;
  data?: unknown[];
  emptyContainerStyle?: React.CSSProperties;
  hideNoDataMessage?: boolean;
  initialLoader?: ReactNode;
};

const ListEmptyResult: React.FC<ListEmptyResultProps> = ({
                                                           loading,
                                                           title,
                                                           actionTitle,
                                                           noDataMessage = 'No data found',
                                                           onClick,
                                                           data,
                                                           emptyContainerStyle,
                                                           hideNoDataMessage,
                                                           initialLoader,
                                                         }) => {
  if (loading && initialLoader && data?.length === 0) {
    return <>{initialLoader}</>;
  } else if (loading) {
    return (
      <StyledEmptyListContainer style={emptyContainerStyle}>
        <Spin/>
      </StyledEmptyListContainer>
    );
  } else {
    return hideNoDataMessage ? null : (
      <StyledEmptyListContainerFlex style={emptyContainerStyle}>
        {title ? <h4>{title}</h4> : null}
        <span>{noDataMessage}</span>

        {actionTitle ? (
          <Button
            type="primary"
            style={{marginTop: 30, minWidth: 150}}
            onClick={onClick}
          >
            {actionTitle}
          </Button>
        ) : null}
      </StyledEmptyListContainerFlex>
    );
  }
};

export default ListEmptyResult;
