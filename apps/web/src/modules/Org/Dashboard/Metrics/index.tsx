import React, { useEffect, useMemo } from 'react';
import { Typography } from 'antd';
import { GoArrowDownRight, GoArrowUpRight } from 'react-icons/go';
import AppGrid from '@unpod/components/common/AppGrid';

import {
  StyledCard,
  StyledChange,
  StyledHeading,
  StyledMetricValue,
  StyledSection,
  StyledValueRow,
} from './index.styled';
import { useAuthContext, useGetDataApi } from '@unpod/providers';
import AppLoader from '@unpod/components/common/AppLoader';
import { getAmountWithCurrency } from '@unpod/helpers/CurrencyHelper';
import { useIntl } from 'react-intl';

const { Text } = Typography;

type Metric = {
  id?: string | number;
  name?: string;
  value?: string | number;
  unit?: string;
  growth?: number;
  trend?: string;
  metric_type?: string;
};

const getValue = (value: string | number, unit?: string) => {
  const stringValue = typeof value === 'number' ? value.toString() : value;
  switch (unit) {
    case 'duration':
      return parseFloat(stringValue).toFixed(2) + ' mins';
    case 'number':
      return parseInt(stringValue, 10).toLocaleString();
    case 'currency': {
      const conversionRate = 88.8;
      const converted = (parseFloat(stringValue) * conversionRate).toFixed(2);
      return getAmountWithCurrency(converted, 'INR');
    }
    default:
      return stringValue;
  }
};

type SingleMetricCardProps = {
  name?: string;
  value?: string | number;
  unit?: string;
  growth?: number;
  trend?: string;
};

const SingleMetricCard: React.FC<SingleMetricCardProps> = ({
  name,
  value = '',
  unit,
  growth = 0,
  trend,
}) => {
  const isPositive = trend === 'positive';
  const ArrowIcon = isPositive ? GoArrowUpRight : GoArrowDownRight;
  const color = isPositive ? '#00c16b' : '#ff4d4f';

  return (
    <StyledCard>
      <Text style={{ color: '#333', fontSize: 16, fontWeight: 500 }}>
        {name}
      </Text>
      <StyledValueRow>
        <StyledMetricValue>{getValue(value, unit)}</StyledMetricValue>
        <StyledChange color={color}>
          <ArrowIcon size={14} />
          {growth > 0 && <span>{growth}%</span>}
        </StyledChange>
      </StyledValueRow>
    </StyledCard>
  );
};

const Metrics = () => {
  const { activeOrg, isAuthenticated } = useAuthContext();
  const { formatMessage } = useIntl();
  const [{ apiData, loading }, { reCallAPI }] = useGetDataApi(
    'metrics/organization/',
    { data: [] as Metric[] },
    {},
    false,
  );

  useEffect(() => {
    if (isAuthenticated && activeOrg) {
      reCallAPI();
    }
  }, [isAuthenticated, activeOrg]);

  const metricsData = useMemo(() => {
    return apiData?.data?.reduce<{ agents: Metric[]; telephony: Metric[] }>(
      (acc, data) => {
        if (data.metric_type === 'agents') {
          acc.agents.push(data);
        } else if (data.metric_type === 'telephony') {
          acc.telephony.push(data);
        }
        return acc;
      },
      { agents: [], telephony: [] },
    );
  }, [apiData?.data]);

  if (loading) {
    return (
      <div style={{ position: 'relative' }}>
        <AppLoader />
      </div>
    );
  }
  return (
    <StyledSection>
      <StyledHeading level={4}>
        {formatMessage({ id: 'downloadLogs.agents' })}
      </StyledHeading>
      <AppGrid
        data={metricsData.agents || []}
        itemPadding={24}
        responsive={{
          xs: 1,
          sm: 2,
          md: 2,
          lg: 4,
        }}
        renderItem={(metric) => (
          <SingleMetricCard key={metric.id} {...metric} />
        )}
      />
      {metricsData.telephony.length > 0 && (
        <>
          <StyledHeading level={4}>Telephony</StyledHeading>
          <AppGrid
            data={metricsData.telephony || []}
            itemPadding={24}
            responsive={{
              xs: 1,
              sm: 2,
              md: 2,
              lg: 4,
            }}
            renderItem={(metric) => (
              <SingleMetricCard key={metric.id} {...metric} />
            )}
          />
        </>
      )}
    </StyledSection>
  );
};

export default Metrics;
