import { Button, Flex } from 'antd';
import AppGrid from '@unpod/components/common/AppGrid';
import CardWrapper from '../../CardWrapper';
import {
  StyledLeft,
  StyledMetricContainer,
  StyledMetricValue,
  StyledName,
  StyledSection,
  StyledSubText,
  StyledValueWrapper,
} from './index.styled';

import { useDownloadData } from '@unpod/providers';
import { getColumns } from './columns';
import { useIntl } from 'react-intl';

type UsageStatsCardsProps = {
  subscription: any;
  [key: string]: any;
};

const UsageStatsCards = ({
  subscription,
  ...restProps
}: UsageStatsCardsProps) => {
  const invoice_number = subscription?.invoice.invoice_number || '';
  const { formatMessage } = useIntl();

  const { downloading, downloadData } = useDownloadData(
    `subscriptions/user-invoices/${invoice_number}/download/`,
    `invoice-${invoice_number}.pdf`,
    'application/pdf',
    'arraybuffer',
  );

  return (
    <StyledSection {...restProps}>
      <AppGrid
        data={getColumns(subscription, formatMessage)}
        itemPadding={24}
        responsive={{
          xs: 1,
          sm: 2,
          md: 2,
          lg: 3,
        }}
        containerStyle={{ marginTop: 0 }}
        renderItem={(metric: any) => (
          <CardWrapper key={metric.id} title="" subtitle="" desc="">
            <StyledMetricContainer>
              <StyledLeft>
                {metric.icon}
                <Flex vertical>
                  <StyledName>{metric.name}</StyledName>
                  <StyledValueWrapper>
                    <StyledMetricValue>
                      {metric.value} {metric.unit}
                    </StyledMetricValue>
                  </StyledValueWrapper>
                  <StyledSubText>{metric.subText}</StyledSubText>
                </Flex>
              </StyledLeft>
              {metric.id === 'currentInvoice' && invoice_number && (
                <Button
                  size="small"
                  disabled={downloading}
                  loading={downloading}
                  onClick={() => downloadData()}
                >
                  {formatMessage({ id: 'common.download' })}
                </Button>
              )}
            </StyledMetricContainer>
          </CardWrapper>
        )}
      />
    </StyledSection>
  );
};

export default UsageStatsCards;
