'use client';
import {forwardRef, useEffect, useImperativeHandle} from 'react';
import {useAuthContext, useGetDataApi} from '@unpod/providers';
import AppGrid from '@unpod/components/common/AppGrid';
import CallStatusBreakdown from './CallStatus';
import MetricItem from './MetricItem';
import {callAnalyticsData, getCallAnalyticsData, getCallStatusData,} from './data';
import {StyledCardContainer, StyledRoot} from './index.styled';
import AnalyticsSkeleton from '@unpod/skeleton/AnalyticsSkeleton';

const AppGridAny = AppGrid as any;

const Dashboard = ({currentSpace}: { currentSpace: any }, ref: any) => {
  const {isAuthenticated} = useAuthContext();

  const [{apiData, loading}, {reCallAPI}] = useGetDataApi(
    `spaces/${currentSpace?.slug}/analytics/`,
    {data: []},
    {},
    false,
  ) as any;
  useEffect(() => {
    if (currentSpace?.slug && isAuthenticated) {
      reCallAPI();
    }
  }, [currentSpace?.slug, isAuthenticated]);

  useImperativeHandle(ref, () => ({
    refreshData: () => {
      reCallAPI();
    },
  }));

  const getValue = (data: any) => {
    if (data)
      return callAnalyticsData.map((item) => ({
        ...item,
        value: data[item.id] !== undefined ? data[item.id] : item.value,
      }));
    return callAnalyticsData;
  };

  return (
    <StyledRoot
      style={{
        padding: '16px',
      }}
    >
      {loading ? (
        <AnalyticsSkeleton/>
      ) : (
        <StyledCardContainer>
          <AppGridAny
            containerStyle={{marginBottom: 0, marginTop: 0}}
            data={getValue(apiData?.data?.call_analytics)}
            itemPadding={24}
            responsive={{
              xs: 1,
              sm: 2,
              md: 2,
              lg: 4,
            }}
            renderItem={(metric: any) => (
              <MetricItem key={metric.id} {...metric} />
            )}
          />

          <CallStatusBreakdown
            data={getCallStatusData(apiData?.data?.call_status)}
          />

          <CallStatusBreakdown
            title="analytics.overview"
            data={getCallAnalyticsData(apiData?.data?.call_analytics)}
          />
        </StyledCardContainer>
      )}
    </StyledRoot>
  );
};

export default forwardRef(Dashboard);
