import {useEffect, useState} from 'react';
import {StyledContainer, StyledRoot, StyledSummaryCard} from './index.styled';
import {IoCalendarOutline, IoDocumentTextOutline, IoEyeOutline, IoPlayCircleOutline,} from 'react-icons/io5';
import {GrActions} from 'react-icons/gr';
import {HiOutlineDatabase} from 'react-icons/hi';

import {MdOutlineBarChart} from 'react-icons/md';
import AppMarkdownViewer from '@unpod/components/third-party/AppMarkdownViewer';
import {getDataApi, useAppSpaceContext, useInfoViewActionsContext,} from '@unpod/providers';
import {AppDrawer} from '@unpod/components/antd';
import AppJsonViewer from '@unpod/components/third-party/AppJsonViewer';
import {formatDuration} from '@unpod/helpers/DateHelper';
import Metrics from '../../../components/Metrics';
import HeadingView from '../../../components/HeadingView';
import {Flex, List, Space, Tag, Typography} from 'antd';
import AppList from '@unpod/components/common/AppList';
import {useIntl} from 'react-intl';
import {IoMdClose} from 'react-icons/io';
import {AppHeaderButton} from '@unpod/components/common/AppPageHeader';
import {useMediaQuery} from 'react-responsive';
import {TabWidthQuery} from '@unpod/constants';
import {PeopleOverviewSkeleton} from '@unpod/skeleton/PeopleOverviewSkeleton';

const {Text} = Typography;

const Summary = () => {
  const {activeCall} = useAppSpaceContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const {formatMessage} = useIntl();

  const [showOutputDrawer, setShowOutputDrawer] = useState(false);

  const overview = activeCall?.output?.post_call_data?.summary || {};
  const recordingUrl =
    activeCall?.recording_url || activeCall?.output?.recording_url;
  const [playingUrl, setPlayingUrl] = useState<string | null>(null);
  const isTablet = useMediaQuery(TabWidthQuery);

  // Helper function to convert agent slug to readable name
  const getAgentNameFromSlug = (slug?: string) => {
    if (!slug) return null;
    // Split by dash, remove last part (random string), and capitalize each word
    const parts = slug.split('-');
    return parts
      .slice(0, -1) // Remove the last part (random string)
      .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  useEffect(() => {
    if (recordingUrl)
      getDataApi('media/pre-signed-url/', infoViewActionsContext, {
        url: recordingUrl,
      }).then((res: any) => {
        setPlayingUrl(res?.data?.url);
      });
  }, [recordingUrl]);

  // Helper function to parse next_action into array
  const getNextActionItems = () => {
    const nextAction =
      activeCall?.output?.post_call_data?.profile_summary?.next_action;
    if (!nextAction) return [];

    // If it's already an array, return it
    if (Array.isArray(nextAction)) return nextAction;

    // If it's a string, try to split by newlines or bullet points
    if (typeof nextAction === 'string') {
      return nextAction
        .split(/\n|•|-/)
        .map((item) => item.trim())
        .filter((item) => item.length > 0);
    }

    return [];
  };

  // Helper function to get follow-up data
  const getFollowUpData = () => {
    return activeCall?.output?.post_call_data?.follow_up || null;
  };

  // Helper function to format follow-up date
  const formatFollowUpDate = (dateString: any) => {
    if (!dateString) return 'Not specified';
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch (error) {
      return dateString;
    }
  };

  // Helper function to get status color
  const getStatusColor = (status: any) => {
    if (!status) return 'default';
    switch (status) {
      case 'call_scheduled':
        return 'success';
      case 'failed to schedule_call':
        return 'error';
      default:
        return 'default';
    }
  };

  // Helper function to format status text
  const formatStatusText = (status: any) => {
    if (!status) return 'Unknown';
    switch (status) {
      case 'call_scheduled':
        return 'Call Scheduled';
      case 'failed to schedule_call':
        return 'Failed to Schedule Call';
      default:
        return status;
    }
  };

  // Helper function to get structured data for metrics
  const getStructuredDataMetrics = () => {
    const structuredData = activeCall?.output?.post_call_data?.structured_data
      ? activeCall?.output?.post_call_data?.structured_data
      : null;
    if (!structuredData || typeof structuredData !== 'object') return [];

    return Object.entries(structuredData)
      .filter(
        ([_, value]) => value !== null && value !== undefined && value !== '',
      )
      .map(([key, value]) => ({
        key,
        label: key
          .split('_')
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' '),
        value:
          typeof value === 'object' ? JSON.stringify(value) : String(value),
      }));
  };

  const metricsData = [
    {
      key: 'interest_level',
      label: formatMessage({id: 'callSummary.interestLevel'}),
      value:
      activeCall?.output?.post_call_data?.profile_summary?.interest_level,
    },
    {
      key: 'agent_details',
      label: formatMessage({id: 'callSummary.agent'}),
      value: getAgentNameFromSlug(activeCall?.assignee),
      link: activeCall?.assignee ? `/ai-studio/${activeCall?.assignee}/` : null,
    },
    {
      key: 'outcome',
      label: formatMessage({id: 'callSummary.outcome'}),
      value: activeCall?.output?.post_call_data?.profile_summary?.outcome,
    },
    {
      key: 'cost',
      label: formatMessage({id: 'callSummary.cost'}),
      value: activeCall?.output?.cost
        ? `$${activeCall?.output?.cost.toFixed(4)}`
        : formatMessage({id: 'callSummary.notAvailable'}),
    },
    {
      key: 'tone',
      label: formatMessage({id: 'callSummary.tone'}),
      value: activeCall?.output?.post_call_data?.profile_summary?.tone,
    },
    {
      key: 'engagement',
      label: formatMessage({id: 'callSummary.engagement'}),
      value: activeCall?.output?.post_call_data?.profile_summary?.engagement,
    },
    {
      key: 'average_call_duration',
      label: formatMessage({id: 'callSummary.averageCallDuration'}),
      value: formatDuration(activeCall?.output?.duration),
    },
    {
      key: 'sentiment_score',
      label: formatMessage({id: 'callSummary.sentimentScore'}),
      value: activeCall?.output?.santiment,
    },
    ...(activeCall?.input?.call_type !== 'inbound'
      ? [
        {
          key: 'call_triggered_by',
          label: formatMessage({id: 'callSummary.callTriggeredBy'}),
          value: activeCall?.user_info?.full_name,
        },
      ]
      : []),
  ];
  const metricsDataWithExtra = metricsData.map((item) => ({
    ...item,
    extra: null,
  }));

  if (!activeCall?.output) {
    return <PeopleOverviewSkeleton/>;
  }


  return (
    <StyledRoot>
      <StyledContainer>
        <HeadingView
          icon={<IoDocumentTextOutline/>}
          name={formatMessage({id: 'callSummary.summary'})}
          extra={
            activeCall?.output && (
              <div
                style={{cursor: 'pointer'}}
                onClick={() => setShowOutputDrawer(true)}
              >
                <IoEyeOutline size={20}/>
              </div>
            )
          }
        />
        <StyledSummaryCard variant="borderless">
          <AppMarkdownViewer
            markdown={
              overview?.summary ||
              formatMessage({id: 'callSummary.noSummary'})
            }
          />
        </StyledSummaryCard>

        {/* Recording Player */}
        {playingUrl && (
          <>
            <HeadingView
              icon={<IoPlayCircleOutline/>}
              name={formatMessage({id: 'callSummary.callRecording'})}
            />
            <StyledSummaryCard bordered={false}>
              <audio
                controls
                style={{width: '100%'}}
                src={playingUrl}
                controlsList={formatMessage({id: 'common.download'})}
              >
                {formatMessage({id: 'callSummary.browserSupportMessage'})}
              </audio>
            </StyledSummaryCard>
          </>
        )}

        {/* Page Header */}
        <HeadingView
          icon={<MdOutlineBarChart/>}
          name={formatMessage({id: 'callSummary.analytics'})}
        />
        <Metrics data={metricsDataWithExtra}/>

        {getNextActionItems().length > 0 && (
          <>
            <HeadingView
              icon={<GrActions size={18}/>}
              name={formatMessage({id: 'callSummary.nextAction'})}
            />
            <AppList
              size="small"
              data={getNextActionItems()}
              renderItem={(item, index) => (
                <List.Item>
                  {index + 1}. {item}
                </List.Item>
              )}
            />
          </>
        )}

        {/* Follow-up Action Widget */}
        {getFollowUpData() && (
          <>
            <HeadingView
              icon={<IoCalendarOutline size={20}/>}
              name={formatMessage({id: 'callSummary.followUp'})}
            />
            <StyledSummaryCard variant="borderless">
              <Space
                orientation="vertical"
                size="middle"
                style={{width: '100%'}}
              >
                {/* Required Status */}
                <div>
                  <Text strong>
                    {formatMessage({id: 'common.required'})}:{' '}
                  </Text>
                  <Tag
                    color={
                      getFollowUpData()?.required === 'true' ||
                      getFollowUpData()?.required === true
                        ? 'blue'
                        : 'default'
                    }
                  >
                    {getFollowUpData()?.required === 'true' ||
                    getFollowUpData()?.required === true
                      ? formatMessage({id: 'common.yes'})
                      : formatMessage({id: 'common.no'})}
                  </Tag>
                </div>

                {/* Scheduled Time */}
                {getFollowUpData()?.time &&
                  getFollowUpData()?.time !== 'N/A' && (
                    <div>
                      <Text strong>
                        {formatMessage({id: 'callSummary.scheduledTime'})}
                        :{' '}
                      </Text>
                      <Text>{formatFollowUpDate(getFollowUpData()?.time)}</Text>
                    </div>
                  )}

                {/* Status */}
                {getFollowUpData()?.status && (
                  <div>
                    <Text strong>
                      {formatMessage({id: 'table.status'})}:{' '}
                    </Text>
                    <Tag color={getStatusColor(getFollowUpData()?.status)}>
                      {formatStatusText(getFollowUpData()?.status)}
                    </Tag>
                  </div>
                )}

                {/* Reason */}
                {getFollowUpData()?.reason && (
                  <div>
                    <Text strong>
                      {formatMessage({id: 'callSummary.reason'})}:{' '}
                    </Text>
                    <Text>{getFollowUpData()?.reason}</Text>
                  </div>
                )}
              </Space>
            </StyledSummaryCard>
          </>
        )}

        {/* Structured Data Section */}
        {getStructuredDataMetrics().length > 0 && (
          <div
            style={{
              width: '100%',
              display: 'flex',
              flexDirection: 'column',
              gap: '5px',
            }}
          >
            <HeadingView
              icon={<HiOutlineDatabase size={20}/>}
              name={formatMessage({id: 'callSummary.structuredData'})}
            />
            <Metrics data={getStructuredDataMetrics()}/>
          </div>
        )}
      </StyledContainer>

      {/* Output Drawer */}
      <AppDrawer
        title={
          <Flex align="center" justify="space-between">
            {formatMessage({id: 'callSummary.callOutput'})}
            <AppHeaderButton
              shape="circle"
              icon={<IoMdClose size={16}/>}
              onClick={() => setShowOutputDrawer(false)}
            />
          </Flex>
        }
        padding="0"
        open={showOutputDrawer}
        onClose={() => setShowOutputDrawer(false)}
        destroyOnClose={true}
        styles={{body: {padding: 0, position: 'relative'}}}
        size={isTablet ? '100%' : 'calc(100% - 405px)'}
      >
        {activeCall?.output && (
          <AppJsonViewer
            json={
              typeof activeCall.output === 'string'
                ? JSON.parse(activeCall.output)
                : activeCall.output
            }
          />
        )}
      </AppDrawer>
    </StyledRoot>
  );
};

export default Summary;
