import {StyledDot, StyledFlex, StyledFlexItem, StyledText,} from './index.styled';
import {Flex, Typography} from 'antd';
import {getFormattedDate} from '@unpod/helpers/DateHelper';
import {AppStatusBadge} from '@unpod/components/common/AppStatusBadge';
import {formatString} from '@unpod/helpers/StringHelper';
import {useIntl} from 'react-intl';
import type {Call} from '@unpod/constants/types';

const {Paragraph} = Typography;

type RenderDescriptionProps = {
  item: Call;
};

export const RenderDescription = ({item}: RenderDescriptionProps) => {
  const {formatMessage} = useIntl();
  const summary =
    item?.output?.post_call_data?.summary?.summary || item?.output?.error || '';
  const labels = item.output?.post_call_data?.classification?.labels ?? [];

  return (
    <Flex vertical gap={summary && 6}>
      <Paragraph
        style={{margin: 0}}
        type="secondary"
        ellipsis={{
          rows: 2,
          expandable: true,
          symbol: formatMessage({id: 'common.readMore'}),
          onExpand: (e) => {
            e.stopPropagation();
          },
        }}
      >
        {summary}
      </Paragraph>

      <StyledFlex gap={8} align="center">
        <StyledText type="secondary">
          {`${
            item.status === 'pending' ? 'Due' : formatString(item.status)
          }: ${getFormattedDate(item.created, 'YYYY-MM-DD HH:mm', true)}`}
        </StyledText>

        {labels.length > 0 && (
          <StyledFlexItem align="center">
            <StyledDot/>
            {labels.map((label) => (
              <AppStatusBadge
                key={label}
                status={label}
                name={label}
                size="small"
              />
            ))}
          </StyledFlexItem>
        )}
      </StyledFlex>
    </Flex>
  );
};
