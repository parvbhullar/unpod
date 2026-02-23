import {StyledDot, StyledFlex, StyledText} from './index.styled';
import {Flex} from 'antd';
import {changeDateStringFormat} from '@unpod/helpers/DateHelper';
import {AppStatusBadge} from '@unpod/components/common/AppStatusBadge';

const statusColors = {
  interested: {color: 'badge-success', label: 'Interested'},
  interrested: {color: 'badge-success', label: 'Interested'},
  'not connected': {color: 'badge-error', label: 'Not Connected'},
  'follow up': {color: 'badge-warning', label: 'Follow Up'},
  connected: {color: 'badge-primary', label: 'Connected'},
};

export const RenderDescription = ({item}: { item: any }) => {
  console.log(
    'RenderDescription item:',
    item.output?.post_call_data?.classification?.labels,
  );
  return (
    <Flex vertical gap={6}>
      {/*<Paragraph*/}
      {/*  style={{ margin: 0 }}*/}
      {/*  type="secondary"*/}
      {/*  ellipsis={{ rows: 2, expandable: true, symbol: 'more' }}*/}
      {/*>*/}
      {/*  {summary}*/}
      {/*</Paragraph>*/}

      <StyledFlex gap={8} align="center">
        <StyledText type="secondary" className="text-capitalize">
          {`${
            item.status === 'panding' ? 'Due' : item.status
          }: ${changeDateStringFormat(item.created, 'YYYY-MM-DD HH:mm:ss')}`}
        </StyledText>

        {item.output?.post_call_data?.classification?.labels?.length !== 0 && (
          <>
            <StyledDot/>
            <AppStatusBadge
              status={item.output?.post_call_data?.classification?.labels?.[0]?.toLowerCase()}
              name={item.output?.post_call_data?.classification?.labels?.[0]?.toLowerCase()}
              size="small"
              statusColors={statusColors}
            />
          </>
        )}
      </StyledFlex>
    </Flex>
  );
};
