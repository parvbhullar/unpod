import { Typography } from 'antd';
import { GoArrowDownRight, GoArrowUpRight } from 'react-icons/go';

import {
  StyledCard,
  StyledChange,
  StyledMetricValue,
  StyledValueRow,
} from './index.styled';
import { getAmountWithCurrency } from '@unpod/helpers/CurrencyHelper';
import { useIntl } from 'react-intl';

const { Text } = Typography;

const getValue = (value: any, unit: any) => {
  switch (unit) {
    case 'duration':
      return parseFloat(value).toFixed(2) + ' mins';
    case 'number':
      return parseInt(value, 10).toLocaleString();
    case 'percentage':
      return parseFloat(value).toFixed(2) + '%';
    case 'currency': {
      const conversionRate = 88.8;
      value = (parseFloat(value) * conversionRate).toFixed(2);
      return getAmountWithCurrency(value, 'INR');
    }
    default:
      return value;
  }
};

const MetricItem = ({
  name,
  value,
  unit,
  growth,
  trend,
}: {
  name: any;
  value: any;
  unit: any;
  growth: any;
  trend: any;
}) => {
  const { formatMessage } = useIntl();
  const isPositive = trend === 'positive';
  const ArrowIcon = isPositive ? GoArrowUpRight : GoArrowDownRight;
  const color = isPositive ? '#00c16b' : '#ff4d4f';

  return (
    <StyledCard>
      <Text style={{ fontSize: 16, fontWeight: 100 }} color="secondary">
        {formatMessage({ id: name })}
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
export default MetricItem;
