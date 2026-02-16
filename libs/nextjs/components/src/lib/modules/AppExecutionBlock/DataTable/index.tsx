import type { Key, ReactNode } from 'react';
import { useEffect, useMemo } from 'react';

import { Form, Input, InputNumber, Tabs } from 'antd';
import type { TableRowSelection } from 'antd/es/table/interface';
import { useFetchDataApi } from '@unpod/providers';
import AppLoader from '../../../common/AppLoader';
import AppTable from '../../../third-party/AppTable';
import { StyledRoot } from './index.styled';

const items = [
  {
    key: 'collection',
    label: 'Collection',
    // children: 'Content of Tab Pane Collection',
  },
  {
    key: 'logs',
    label: 'Logs',
    // children: 'Content of Tab Pane Logs',
  },
  {
    key: 'files',
    label: 'Files',
    // children: 'Content of Tab Pane Files',
  },
];

/*const originData = [];
for (let i = 0; i < 100; i++) {
  originData.push({
    key: i.toString(),
    name: `Edward ${i}`,
    age: 32,
    address: `London Park no. ${i}`,
  });
}*/

type EditableCellProps = {
  editing: boolean;
  dataIndex: string;
  title: string;
  inputType: 'number' | 'text';
  record: any;
  index: number;
  children: ReactNode;
  [key: string]: any;};

const EditableCell = ({
  editing,
  dataIndex,
  title,
  inputType,
  record,
  index,
  children,
  ...restProps
}: EditableCellProps) => {
  const inputNode = inputType === 'number' ? <InputNumber /> : <Input />;
  return (
    <td {...restProps}>
      {editing ? (
        <Form.Item
          name={dataIndex}
          style={{
            margin: 0,
          }}
          rules={[
            {
              required: true,
              message: `Please Input ${title}!`,
            },
          ]}
        >
          {inputNode}
        </Form.Item>
      ) : (
        children
      )}
    </td>
  );
};

type DataTableProps = {
  threadId?: string;
  superbookHandle?: string;};

const DataTable = ({ threadId, superbookHandle }: DataTableProps) => {
  const [form] = Form.useForm();
  /*const [data, setData] = useState(originData);
  const [editingKey, setEditingKey] = useState('');*/

  const [{ apiData, loading }, { updateInitialUrl }] = useFetchDataApi<any>(
    `core/pilots/${superbookHandle}/data/${threadId}/`,
    [],
    {},
    false,
  );

  useEffect(() => {
    if (threadId && superbookHandle) {
      updateInitialUrl(`core/pilots/${superbookHandle}/data/${threadId}/`);
    }
  }, [threadId, superbookHandle]);

  const columns = useMemo(() => {
    if (apiData?.columns) {
      return apiData.columns.map((column: string) => ({
        title: column,
        dataIndex: column,
        editable: true,
      }));
    }

    return [];
  }, [apiData?.columns]);

  /*const isEditing = (record) => record.key === editingKey;
  const edit = (record) => {
    form.setFieldsValue({
      name: '',
      age: '',
      address: '',
      ...record,
    });
    setEditingKey(record.key);
  };*/

  /*const cancel = () => {
    setEditingKey('');
  };

  const save = async (key) => {
    try {
      const row = await form.validateFields();
      const newData = [...data];
      const index = newData.findIndex((item) => key === item.key);
      if (index > -1) {
        const item = newData[index];
        newData.splice(index, 1, {
          ...item,
          ...row,
        });
        setData(newData);
        setEditingKey('');
      } else {
        newData.push(row);
        setData(newData);
        setEditingKey('');
      }
    } catch (errInfo) {
      console.log('Validate Failed:', errInfo);
    }
  };*/

  /*const columns = [
    {
      title: 'name',
      dataIndex: 'name',
      width: '25%',
      editable: true,
    },
    {
      title: 'age',
      dataIndex: 'age',
      width: '15%',
      editable: true,
    },
    {
      title: 'address',
      dataIndex: 'address',
      width: '40%',
      editable: true,
    },
    {
      title: 'operation',
      dataIndex: 'operation',
      render: (_, record) => {
        const editable = isEditing(record);
        return editable ? (
          <span>
            <Typography.Link
              onClick={() => save(record.key)}
              style={{
                marginRight: 8,
              }}
            >
              Save
            </Typography.Link>
            <Popconfirm title="Sure to cancel?" onConfirm={cancel}>
              <a>Cancel</a>
            </Popconfirm>
          </span>
        ) : (
          <Typography.Link
            disabled={editingKey !== ''}
            onClick={() => edit(record)}
          >
            Edit
          </Typography.Link>
        );
      },
    },
  ];*/

  /*const mergedColumns = columns.map((col) => {
    if (!col.editable) {
      return col;
    }
    return {
      ...col,
      onCell: (record) => ({
        record,
        inputType: col.dataIndex === 'age' ? 'number' : 'text',
        dataIndex: col.dataIndex,
        title: col.title,
        editing: isEditing(record),
      }),
    };
  });*/

  const rowSelection: TableRowSelection<any> = {
    type: 'checkbox',
    onChange: (selectedRowKeys: Key[], selectedRows: any[]) => {
      console.log(
        `selectedRowKeys: ${selectedRowKeys}`,
        'selectedRows: ',
        selectedRows,
      );
    },
  };

  return (
    <StyledRoot>
      <Tabs defaultActiveKey="collection" items={items} />

      <Form form={form} component={false}>
        <AppTable
          components={{
            body: {
              cell: EditableCell,
            },
          }}
          rowKey={(record) => apiData?.data?.indexOf(record)}
          rowSelection={rowSelection}
          dataSource={apiData?.data || []}
          columns={columns || []}
          rowClassName="editable-row"
          pagination={false}
        />
      </Form>

      {loading && <AppLoader />}
    </StyledRoot>
  );
};

export default DataTable;
