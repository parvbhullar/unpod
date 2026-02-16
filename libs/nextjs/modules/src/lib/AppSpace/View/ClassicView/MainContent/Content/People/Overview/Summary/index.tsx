import { IoDocumentTextOutline } from 'react-icons/io5';
import { MdOutlineBarChart } from 'react-icons/md';
import AppMarkdownViewer from '@unpod/components/third-party/AppMarkdownViewer';
import { getTimeFromNow } from '@unpod/helpers/DateHelper';
import Metrics from '../../../components/Metrics';
import HeadingView from '../../../components/HeadingView';
import {
  StyledContainer,
  StyledRoot,
  StyledSummaryCard,
} from '../../../Calls/Overview/Summary/index.styled';
import { useIntl } from 'react-intl';

type SummaryData = {
  overview?: {
    summary?: string;
    analytics?: {
      total_calls?: string | number;
      connected_calls?: string | number;
      last_connected?: string;
      avg_call_duration?: string | number;
      response_rate?: string | number;
      preferred_time?: string | number;
      sentiment?: string | number;
      [key: string]: unknown;
    };
  };
  labels?: string[];
};

type SummaryProps = {
  data: SummaryData | null;
};

const Summary = ({ data }: SummaryProps) => {
  const analytics = data?.overview?.analytics || {};
  const { formatMessage } = useIntl();

  const analyticsItems = [
    {
      key: 'total_calls',
      label: formatMessage({ id: 'peopleSummary.totalCalls' }),
      value: analytics?.total_calls || '0',
    },
    {
      key: 'connected_calls',
      label: formatMessage({ id: 'peopleSummary.connectedCalls' }),
      value: analytics?.connected_calls || '0',
    },
    {
      key: 'last_connected',
      label: formatMessage({ id: 'peopleSummary.lastConnected' }),
      value: analytics?.last_connected
        ? getTimeFromNow(analytics?.last_connected)
        : 'N/A',
    },
    {
      key: 'profile_status',
      label: formatMessage({ id: 'peopleSummary.profileStatus' }),
      value: data?.labels ? data?.labels[0] : 'N/A',
    },
    {
      key: 'average_call_duration',
      label: formatMessage({ id: 'peopleSummary.averageCallDuration' }),
      value: analytics?.avg_call_duration || 'N/A',
    },
    {
      key: 'response_rate',
      label: formatMessage({ id: 'peopleSummary.responseRate' }),
      value: analytics?.response_rate || 'N/A',
    },
    {
      key: 'preferred_time',
      label: formatMessage({ id: 'peopleSummary.preferredTime' }),
      value: analytics?.preferred_time || 'N/A',
    },
    {
      key: 'sentiment_score',
      label: formatMessage({ id: 'peopleSummary.sentimentScore' }),
      value: analytics?.sentiment || 'N/A',
    },
  ];

  return (
    <StyledRoot>
      <StyledContainer>
        <HeadingView
          icon={<IoDocumentTextOutline />}
          name={formatMessage({ id: 'peopleSummary.title' })}
        />

        <StyledSummaryCard bordered={false}>
          <AppMarkdownViewer
            markdown={
              data?.overview?.summary ||
              formatMessage({ id: 'peopleSummary.noDataFound' })
            }
          />
        </StyledSummaryCard>

        <HeadingView
          icon={<MdOutlineBarChart />}
          name={formatMessage({ id: 'peopleSummary.analytics' })}
        />

        <Metrics data={analyticsItems} />
      </StyledContainer>
    </StyledRoot>
  );
};

export default Summary;
