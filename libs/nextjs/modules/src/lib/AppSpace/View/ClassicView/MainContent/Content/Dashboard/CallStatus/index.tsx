import { Progress } from 'antd';
import {
  IconWrapper,
  ProgressWrapper,
  StatusContent,
  StatusCount,
  StatusItem,
  StatusLabel,
  StatusList,
  StatusPercentage,
  StatusStats,
  StyledCard,
} from './index.styled';
import { useIntl } from 'react-intl';

const CallStatusBreakdown = ({
  title = 'analytics.breakdown',
  data,
  suffix = 'analytics.calls',
}: {
  title?: string;
  data: any[];
  suffix?: string;
}) => {
  const { formatMessage } = useIntl();
  const [total, ...statusConfig] = data;

  const calculatePercentage = (value: any) => {
    if (total.value === 0) return 0;
    return ((value / total.value) * 100).toFixed(1);
  };

  return (
    <StyledCard
      title={formatMessage({ id: title })}
      extra={
        <strong>{`${formatMessage({ id: 'common.total' })} ${(
          total.value | 0
        ).toLocaleString()} ${formatMessage({ id: suffix })}`}</strong>
      }
    >
      <StatusList>
        {statusConfig
          .filter((status) => status.value > 0)
          .map((status) => {
            const percentage =
              status.key.includes('_rate') || status.key.includes('_score')
                ? status.value
                : calculatePercentage(status.value);

            return (
              <StatusItem key={status.key}>
                <IconWrapper $bgColor={status.bgColor} $color={status.color}>
                  {status.icon}
                </IconWrapper>

                <StatusContent>
                  <StatusLabel>
                    {formatMessage({ id: status.label })}
                  </StatusLabel>

                  <ProgressWrapper>
                    <Progress
                      percent={percentage}
                      strokeColor={status.color}
                      trailColor="#f0f0f0"
                      showInfo={false}
                    />
                  </ProgressWrapper>
                </StatusContent>

                <StatusStats>
                  <StatusCount>{status.value.toLocaleString()}</StatusCount>
                  <StatusPercentage>({percentage}%)</StatusPercentage>
                </StatusStats>
              </StatusItem>
            );
          })}
      </StatusList>
    </StyledCard>
  );
};

export default CallStatusBreakdown;
