import AppColumnZoomCell from '@unpod/components/common/AppColumnZoomView/AppColumnZoomCell';
import {changeDateStringFormat} from '@unpod/helpers/DateHelper';

type FormatMessage = (descriptor: { id: string }) => string;
type TaskInput = { name?: string };

export const getColumns = (
  setSelectedCol: (value: any) => void,
  formatMessage: FormatMessage,
) => {
  return [
    {
      title: formatMessage({id: 'task.name'}),
      dataIndex: 'input',
      key: 'input',
      render: (input: TaskInput) => input?.name,
    },
    {
      title: formatMessage({id: 'task.context'}),
      dataIndex: 'task',
      key: 'task',
      render: (value: any) => (
        <AppColumnZoomCell
          title={formatMessage({id: 'task.context'})}
          value={value}
          setSelectedCol={setSelectedCol}
        />
      ),
    },
    {
      title: formatMessage({id: 'task.assignedTo'}),
      dataIndex: 'assignee',
      key: 'assignee',
    },
    {
      title: formatMessage({id: 'task.output'}),
      dataIndex: 'output',
      key: 'output',
      render: (value: any) => (
        <AppColumnZoomCell
          title="Output"
          value={value}
          setSelectedCol={setSelectedCol}
        />
      ),
    },
    {
      title: formatMessage({id: 'task.status'}),
      dataIndex: 'status',
      key: 'status',
    },
    {
      title: formatMessage({id: 'task.createdAt'}),
      dataIndex: 'created',
      key: 'created',
      render: (value: string) =>
        changeDateStringFormat(
          value,
          'YYYY-MM-DD HH:mm:ss',
          'DD-MM-YYYY HH:mm:ss',
        ),
    },
    {
      title: formatMessage({id: 'task.updatedAt'}),
      dataIndex: 'modified',
      key: 'modified',
      render: (value: string) =>
        changeDateStringFormat(
          value,
          'YYYY-MM-DD HH:mm:ss',
          'DD-MM-YYYY HH:mm:ss',
        ),
    },
  ];
};
