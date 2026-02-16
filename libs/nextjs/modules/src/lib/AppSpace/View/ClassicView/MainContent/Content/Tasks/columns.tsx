import { useRef, useState } from 'react';
import { Button, Flex, Tooltip, Typography } from 'antd';
import {
  MdOutlineDownload,
  MdOutlinePause,
  MdOutlinePlayArrow,
} from 'react-icons/md';
import {
  changeDateStringFormat,
  getTimeFromNow,
} from '@unpod/helpers/DateHelper';
import AppColumnZoomCell from '@unpod/components/common/AppColumnZoomView/AppColumnZoomCell';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { AppStatusBadge } from '@unpod/components/common/AppStatusBadge';
import {
  getColumnSearchProps,
  getColumnSelectBoxProps,
  onSortOrder,
} from '@unpod/helpers/TableHelper';
import type { IntlShape } from 'react-intl';
import type { TaskItem } from '@unpod/constants/types';

const { Text } = Typography;

const VIEW_DATA_STATUS = {
  processing: { color: 'badge-primary', label: 'Processing' },
  failed: { color: 'badge-error', label: 'Failed' },
  pending: { color: 'badge-warning', label: 'Pending' },
  completed: { color: 'badge-success', label: 'Completed' },
  in_progress: { color: 'badge-info', label: 'In Progress' },
};
const STATUS_DATA_FILTER = [
  { id: 'pending', name: 'Pending' },
  { id: 'processing', name: 'Processing' },
  { id: 'in_progress', name: 'In Progress' },
  { id: 'completed', name: 'Completed' },
  { id: 'failed', name: 'Failed' },
];

const PlayButton = ({ item }: { item: TaskItem }) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [loading, setLoading] = useState(false);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [isPlaying, setPlaying] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const onPlaySound = () => {
    if (fileUrl) {
      if (!audioRef.current) return;
      if (isPlaying) audioRef.current.pause();
      else audioRef.current.play();
      setPlaying(!isPlaying);
    } else {
      setLoading(true);
      getDataApi<{ url?: string }>(
        'media/pre-signed-url/',
        infoViewActionsContext,
        {
          url: item.output?.recording_url,
        },
      )
        .then((res) => {
          const url = res.data?.url;
          if (!url) {
            infoViewActionsContext.showError('Unable to load audio.');
            setLoading(false);
            return;
          }
          const audio = new Audio(url);
          audioRef.current = audio;
          setFileUrl(url);
          audio.play();
          audio.onended = () => {
            setPlaying(false);
          };
          setLoading(false);
          setPlaying(true);
        })
        .catch((response) => {
          infoViewActionsContext.showError(response.message);
          setLoading(false);
        });
    }
  };

  return isPlaying ? (
    <Tooltip title="Pause">
      <Button
        shape="circle"
        size="small"
        icon={<MdOutlinePause fontSize={18} />}
        onClick={onPlaySound}
        style={{ color: 'red' }} // Change color to indicate pause state
      />
    </Tooltip>
  ) : (
    <Tooltip title="Play">
      <Button
        shape="circle"
        size="small"
        icon={<MdOutlinePlayArrow fontSize={18} />}
        onClick={onPlaySound}
        loading={loading}
      />
    </Tooltip>
  );
};

type SetSelectedCol = (value: unknown) => void;
type OnDownload = (item: TaskItem) => void;

export const getColumns = (
  setSelectedCol: SetSelectedCol,
  onDownload: OnDownload,
  formatMessage: IntlShape['formatMessage'],
) => {
  return [
    {
      title: 'Name',
      dataIndex: 'input',
      key: 'input',
      ...getColumnSearchProps('Name', 'name', formatMessage),
      render: (input: TaskItem['input']) =>
        input?.name || input?.title || 'N/A',
    },
    {
      title: 'Context',
      dataIndex: 'task',
      key: 'task',
      ...getColumnSearchProps('Context', 'task', formatMessage),
      render: (value: unknown) => (
        <AppColumnZoomCell
          title="Context"
          value={value}
          setSelectedCol={setSelectedCol}
        />
      ),
    },
    {
      title: 'Assigned To',
      dataIndex: 'assignee',
      key: 'assignee',
      ...getColumnSearchProps('Assigned To', 'assignee', formatMessage),
    },
    {
      title: 'Output',
      dataIndex: 'output',
      key: 'output',
      render: (value: unknown) => (
        <AppColumnZoomCell
          title="Output"
          value={value}
          setSelectedCol={setSelectedCol}
        />
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      ...getColumnSelectBoxProps(
        'Status',
        'status',
        STATUS_DATA_FILTER,
        formatMessage,
      ),
      render: (text: string) => (
        <AppStatusBadge status={text} statusColors={VIEW_DATA_STATUS} />
      ),
    },
    {
      title: 'Actions',
      dataIndex: 'created',
      key: 'created',
      render: (_value: unknown, item: TaskItem) =>
        item.status === 'completed' &&
        (item.output?.recording_url ? (
          <Flex align="center" gap={10}>
            <Tooltip title="Download">
              <Button
                shape="circle"
                size="small"
                icon={<MdOutlineDownload fontSize={18} />}
                onClick={() => onDownload(item)}
              />
            </Tooltip>
            <PlayButton item={item} />
          </Flex>
        ) : (
          'No Recording'
        )),
    },
    {
      title: 'Created At',
      dataIndex: 'created',
      key: 'created',
      sorter: (a: TaskItem, b: TaskItem) =>
        onSortOrder(a, b, 'created', 'string'),
      render: (value: string) => (
        <Tooltip
          title={changeDateStringFormat(
            value,
            'YYYY-MM-DD HH:mm:ss',
            'hh:mm A . DD MMM, YYYY',
          )}
        >
          <Text>{getTimeFromNow(value)}</Text>
        </Tooltip>
      ),
    },
    /*{
      title: 'Updated At',
      dataIndex: 'modified',
      key: 'modified',
      render: (value) =>
        changeDateStringFormat(
          value,
          'YYYY-MM-DD HH:mm:ss',
          'DD-MM-YYYY HH:mm:ss'
        ),
    },*/
  ];
};
