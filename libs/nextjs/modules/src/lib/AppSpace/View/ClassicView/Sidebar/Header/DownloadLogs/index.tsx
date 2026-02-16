import { useEffect, useState } from 'react';
import { Button, Col, Form, Select } from 'antd';
import {
  downloadDataApi,
  useAppSpaceContext,
  useGetDataApi,
  useInfoViewActionsContext,
  useInfoViewContext,
  usePaginatedDataApi,
} from '@unpod/providers';
import {
  changeDateStringFormat,
  getDateObject,
  getUtcTimestamp,
} from '@unpod/helpers/DateHelper';
import {
  AppDateTime,
  AppGridContainer,
  AppInput,
  AppSelect,
  DrawerBody,
  DrawerForm,
  DrawerFormFooter,
} from '@unpod/components/antd';
import { fileDownload } from '@unpod/helpers/FileHelper';
import { useIntl } from 'react-intl';
import type { Dayjs } from 'dayjs';
import { cleanObject, isEmptyObject } from '@unpod/helpers';

const { Item } = Form;
const { Option } = Select;

type RunItem = {
  run_id?: string;
  created?: string;
  [key: string]: unknown;
};

type AgentItem = {
  handle?: string;
  name?: string;
};

type UserItem = {
  token?: string;
  full_name?: string;
  email?: string;
  role?: string;
  [key: string]: unknown;
};

type DownloadLogsForm = {
  from_ts?: Date | Dayjs;
  to_ts?: Date | Dayjs;
  runs?: string[];
  agents?: string[];
  user_token?: string;
  contact_numbers?: string;
  document_id?: string;
};

type DownloadLogsProps = {
  onClose?: () => void;
};

const DownloadLogs = ({ onClose }: DownloadLogsProps) => {
  const [form] = Form.useForm();
  const [userList, setUserList] = useState<UserItem[]>([]);
  const { currentSpace } = useAppSpaceContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();
  const { loading: downloading } = useInfoViewContext();

  const [{ apiData }, { reCallAPI }] = usePaginatedDataApi(
    `tasks/space-runs/${currentSpace?.token}/`,
    [],
    {
      page: 1,
      page_size: 30,
    },
    false,
  ) as unknown as [{ apiData: RunItem[] }, { reCallAPI: () => void }];

  const [{ apiData: agents }, { setQueryParams, reCallAPI: reCallPilotsAPI }] =
    useGetDataApi(
      `core/pilots/org/`,
      { data: [] },
      { type: 'Voice', search: '' },
      false,
    ) as unknown as [
      { apiData?: { data?: AgentItem[] } },
      {
        setQueryParams: (params: Record<string, unknown>) => void;
        reCallAPI: () => void;
      },
    ];

  // const { downloading, downloadData } = useDownloadData(
  //   `tasks/space-task/${currentSpace?.token}/export/`,
  //   ``,
  // );

  useEffect(() => {
    reCallAPI();
    reCallPilotsAPI();
  }, []);

  useEffect(() => {
    if (currentSpace?.users) {
      const users = (currentSpace.users as UserItem[]) ?? [];
      setUserList(users.filter((item) => item.role !== 'viewer'));
    }
  }, [currentSpace?.users]);

  const onSearch = (value: string) => {
    setQueryParams({ search: value, type: 'Voice' });
  };

  const onSubmitSuccess = (formData: DownloadLogsForm) => {
    let params: Record<string, unknown> = {};
    if (!isEmptyObject(cleanObject(formData))) {
      params = { ...formData };
    }
    if (formData.from_ts) {
      params['from_ts'] = getUtcTimestamp(formData.from_ts);
    }
    if (formData.to_ts) {
      params['to_ts'] = getUtcTimestamp(formData.to_ts);
    }

    if (formData.runs && formData.runs.length > 0) {
      params['runs'] = formData.runs.join(',');
    }

    if (formData.agents && formData.agents.length > 0) {
      params['agents'] = formData.agents.join(',');
    }
    console.log('Form Data Params', params);

    const now = getDateObject();
    downloadDataApi(
      `tasks/space-task/${currentSpace?.token}/export/`,
      infoViewActionsContext,
      params,
    )
      .then((data) => {
        fileDownload(
          data,
          `${formatMessage({ id: 'downloadLogs.fileName' })} - ${now.format(
            'YYYY-MM-DD HH:mm:ss',
          )}.csv`,
        );
        infoViewActionsContext.showMessage(
          formatMessage({ id: 'downloadLogs.success' }),
        );
        onClose?.();
      })
      .catch(() => {
        infoViewActionsContext.showError(
          formatMessage({ id: 'downloadLogs.error' }),
        );
      });

    // downloadData(
    //   params,
    //   `Space Actions Logs - ${now.format('YYYY-MM-DD HH:mm:ss')}.csv`,
    // );
  };

  const onClearForm = () => {
    form.resetFields();
    onClose?.();
  };
  return (
    <DrawerForm form={form} onFinish={onSubmitSuccess}>
      <DrawerBody>
        <AppGridContainer>
          <Col md={12} sm={24}>
            <Item name="from_ts">
              <AppDateTime
                placeholder={formatMessage({ id: 'downloadLogs.from' })}
                showTime={{ format: 'HH:mm:ss' }}
                format="DD-MM-YYYY HH:mm:ss"
              />
            </Item>
          </Col>

          <Col md={12} sm={24}>
            <Item name="to_ts">
              <AppDateTime
                placeholder={formatMessage({ id: 'downloadLogs.to' })}
                showTime={{ format: 'HH:mm:ss' }}
                format="DD-MM-YYYY HH:mm:ss"
              />
            </Item>
          </Col>
        </AppGridContainer>

        <Item name="runs">
          <AppSelect
            placeholder={formatMessage({ id: 'downloadLogs.runIds' })}
            mode="multiple"
            optionLabelProp="label"
            optionFilterProp="children"
            allowClear
          >
            {apiData?.map((item) => (
              <Option key={item.run_id} value={item.run_id}>
                {item.run_id} (
                {changeDateStringFormat(
                  item.created,
                  'YYYY-MM-DD HH:mm:ss',
                  'DD-MM-YYYY HH:mm:ss',
                )}
                )
              </Option>
            ))}
          </AppSelect>
        </Item>

        <Item name="agents">
          <AppSelect
            placeholder={formatMessage({ id: 'downloadLogs.agents' })}
            mode="multiple"
            onSearch={onSearch}
            allowClear
          >
            {agents?.data?.map((agent, index) => (
              <Option key={index} value={agent.handle}>
                {agent.name}
              </Option>
            ))}
          </AppSelect>
        </Item>

        <Item name="user_token">
          <AppSelect placeholder={formatMessage({ id: 'downloadLogs.user' })}>
            {userList.map((user, index) => (
              <Option key={index} value={user.token}>
                {user.full_name || user.email}
              </Option>
            ))}
          </AppSelect>
        </Item>

        <Item name="contact_numbers">
          <AppInput
            placeholder={formatMessage({
              id: 'downloadLogs.contactNumbers',
            })}
          />
        </Item>

        <Item name="document_id">
          <AppInput
            placeholder={formatMessage({ id: 'downloadLogs.documentId' })}
          />
        </Item>
      </DrawerBody>

      <DrawerFormFooter>
        <Button onClick={onClearForm}>
          {formatMessage({ id: 'common.cancel' })}
        </Button>
        <Button type="primary" htmlType="submit" loading={downloading}>
          {formatMessage({ id: 'common.download' })}
        </Button>
      </DrawerFormFooter>
    </DrawerForm>
  );
};

export default DownloadLogs;
