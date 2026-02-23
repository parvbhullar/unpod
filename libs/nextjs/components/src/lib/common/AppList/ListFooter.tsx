import React from 'react';
import {StyledListFooter, StyledRecordCount} from './index.styled';
import AppLoadingMore from '../AppLoadingMore';
import {tablePageSize} from '@unpod/constants';
import {useIntl} from 'react-intl';

type ListFooterProps = {
  loading?: boolean;
  footerText?: string;
  hasMoreRecord?: boolean;
  count?: number;
  showCount?: number;
};

const ListFooter: React.FC<ListFooterProps> = ({
                                                 loading = false,
                                                 footerText = 'call.noMoreRecords',
                                                 hasMoreRecord,
                                                 count = 0,
                                                 showCount = 0,
                                               }) => {
  const {formatMessage} = useIntl();
  return (
    <>
      {showCount > 0 && (
        <StyledRecordCount>
          {formatMessage(
            {id: 'appList.footerShowingRecords'},
            {count, total: showCount},
          )}
        </StyledRecordCount>
      )}

      {loading ? (
        <AppLoadingMore/>
      ) : !hasMoreRecord && count > tablePageSize ? (
        <StyledListFooter>{formatMessage({id: footerText})}</StyledListFooter>
      ) : null}
    </>
  );
};

export default ListFooter;
