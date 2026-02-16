import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  HourglassOutlined,
  LoadingOutlined,
  RiseOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import {
  MdNotInterested,
  MdSignalCellularConnectedNoInternet4Bar,
} from 'react-icons/md';
import { FaPhoneVolume, FaRegPaperPlane, FaSmileBeam } from 'react-icons/fa';
import { BiTimeFive } from 'react-icons/bi';

export const callAnalyticsData = [
  {
    id: 'total_calls',
    name: 'dashboard.totalCalls',
    value: 0,
    unit: 'number',
    growth: 0,
    trend: 'positive',
    status: 'active',
  },
  {
    id: 'interested',
    name: 'dashboard.interestedCalls',
    value: 0,
    unit: 'number',
    growth: 0,
    trend: 'positive',
    status: 'active',
  },
  /*{
    id: 'call_back',
    name: 'Call Backs',
    value: 0,
    unit: 'number',
    growth: 0,
    trend: 'negative',
    status: 'active',
  },*/
  /*{
    id: 'send_details',
    name: 'Details Sent',
    value: 0,
    unit: 'number',
    growth: 0,
    trend: 'positive',
    status: 'active',
  },
  {
    id: 'not_interested',
    name: 'Not Interested',
    value: 0,
    unit: 'number',
    growth: 0,
    trend: 'positive',
    status: 'active',
  },*/
  {
    id: 'not_connected',
    name: 'task.notConnected',
    value: 0,
    unit: 'number',
    growth: 0,
    trend: 'positive',
    status: 'active',
  },
  /*{
    id: 'failed',
    name: 'Failed Calls',
    value: 0,
    unit: 'number',
    growth: 0,
    trend: 'positive',
    status: 'active',
  },*/
  {
    id: 'avg_success_score',
    name: 'dashboard.avgSuccessScore',
    value: 0,
    unit: 'percentage',
    growth: 0,
    trend: 'positive',
    status: 'active',
  },
];

export const getCallAnalyticsData = (data: any) => {
  const defaultData = {
    total_calls: 0,
    interested: 0,
    call_back: 0,
    send_details: 0,
    not_interested: 0,
    not_connected: 0,
    failed: 0,
    avg_success_score: 0,
  };

  const states = data || defaultData;

  return [
    {
      key: 'total_calls',
      label: 'dashboard.totalCalls',
      value: states.total_calls,
      icon: <FaPhoneVolume />,
      color: '#01a6f6',
      bgColor: '#e8f6ff',
    },
    {
      key: 'interested',
      label: 'dashboard.interestedCalls',
      value: states.interested,
      icon: <FaSmileBeam />,
      color: '#52c41a',
      bgColor: '#d4f4dd',
    },
    {
      key: 'call_back',
      label: 'dashboard.callBacks',
      value: states.call_back,
      icon: <BiTimeFive />,
      color: '#faad14',
      bgColor: '#fff7e6',
    },
    {
      key: 'send_details',
      label: 'dashboard.detailsSent',
      value: states.send_details,
      icon: <FaRegPaperPlane />,
      color: '#1c50f6',
      bgColor: '#d6e9ff',
    },
    {
      key: 'not_interested',
      label: 'dashboard.notInterested',
      value: states.not_interested,
      icon: <MdNotInterested />,
      color: '#ff4d4f',
      bgColor: '#ffe5e5',
    },
    {
      key: 'not_connected',
      label: 'dashboard.notConnected',
      value: states.not_connected,
      icon: <MdSignalCellularConnectedNoInternet4Bar />,
      color: '#015706',
      bgColor: '#d6e9ff',
    },
    {
      key: 'failed',
      label: 'dashboard.failedCalls',
      value: states.failed,
      icon: <CloseCircleOutlined />,
      color: '#ff4d4f',
      bgColor: '#ffe5e5',
    },

    /*{
    key: 'avg_success_score',
    label: 'Avg. Success Score',
    value: states.avg_success_score,
    icon: <FaChartLine />,
    color: '#015706',
    bgColor: '#d6e9ff',
  },*/
  ];
};

export const getCallStatusData = (data: any) => {
  const defaultData = {
    total_tasks: 0,
    completed: 0,
    failed: 0,
    pending: 0,
    in_progress: 0,
    success_rate: 0,
  };

  const states = data || defaultData;

  return [
    {
      key: 'total_tasks',
      label: 'common.total',
      value: states.total_tasks,
      icon: <UnorderedListOutlined />,
      color: '#01a6f6',
      bgColor: '#e8f6ff',
    },
    {
      key: 'pending',
      label: 'task.pending',
      value: states.pending,
      icon: <HourglassOutlined />,
      color: '#faad14',
      bgColor: '#fff7e6',
    },
    {
      key: 'in_progress',
      label: 'task.inProgress',
      value: states.in_progress,
      icon: <LoadingOutlined spin />,
      color: '#1c50f6',
      bgColor: '#d6e9ff',
    },
    {
      key: 'completed',
      label: 'task.completed',
      value: states.completed,
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      bgColor: '#d4f4dd',
    },
    {
      key: 'failed',
      label: 'task.failed',
      value: states.failed,
      icon: <CloseCircleOutlined />,
      color: '#ff4d4f',
      bgColor: '#ffe5e5',
    },
    {
      key: 'success_rate',
      label: 'dashboard.completionRate',
      value: states.success_rate,
      icon: <RiseOutlined />,
      color: '#015706',
      bgColor: '#d6e9ff',
    },
  ];
};
