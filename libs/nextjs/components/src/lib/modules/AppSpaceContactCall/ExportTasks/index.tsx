import {Fragment, useEffect, useState} from 'react';

import {Button, Col, Form, Select} from 'antd';
import {MdDownload} from 'react-icons/md';
import {changeDateStringFormat, getDateObject, getUtcTimestamp,} from '@unpod/helpers/DateHelper';
import {useDownloadData, useGetDataApi, usePaginatedDataApi,} from '@unpod/providers';
import AppDrawer from '../../../antd/AppDrawer';
import {AppGridContainer, DrawerBody, DrawerForm, DrawerFormFooter,} from '../../../antd';
import AppInput from '../../../antd/AppInput';
import AppDateTime from '../../../antd/AppDateTime';
import AppSelect from '../../../antd/AppSelect';
import {AppHeaderButton} from '../../../common/AppPageHeader';
import {useIntl} from 'react-intl';
import {Spaces, User} from '@unpod/constants';

const {Item, useForm} = Form;
const {Option} = Select;

type RunItem = {
  run_id: string | number;
  created: string;
};

type AgentItem = {
  handle: string;
  name?: string;
};

type AgentsResponse = {
  data?: AgentItem[];
};

const ExportTasks = ({currentSpace}: { currentSpace: Spaces }) => {
  const [form] = useForm();
  const [open, setOpen] = useState(false);
  const [userList, setUserList] = useState<User[]>([]);
  const {formatMessage} = useIntl();

  const [{apiData: runs}, {reCallAPI}] = usePaginatedDataApi(
    `tasks/space-runs/${currentSpace?.token}/`,
    [],
    {
      page: 1,
      page_size: 30,
    },
    false,
  ) as [{ apiData: RunItem[] }, { reCallAPI: () => void }];

  const [{apiData: agents}, {setQueryParams, reCallAPI: reCallPilotsAPI}] =
    useGetDataApi(
      `core/pilots/org/`,
      {data: []},
      {type: 'Voice', search: ''},
      false,
    ) as [
      { apiData: AgentsResponse },
      {
        setQueryParams: (params: Record<string, unknown>) => void;
        reCallAPI: () => void;
      },
    ];

  const {downloading, downloadData} = useDownloadData(
    `tasks/space-task/${currentSpace?.token}/export/`,
    ``,
  );

  useEffect(() => {
    if (open) {
      reCallAPI();
      reCallPilotsAPI();
    }
  }, [open]);

  useEffect(() => {
    if (currentSpace?.users) {
      setUserList(currentSpace.users?.filter((item) => item.role !== 'viewer'));
    }
  }, [currentSpace?.users]);

  const onSearch = (value: string) => {
    setQueryParams({search: value, type: 'Voice'});
  };

  const onSubmitSuccess = (formData: Record<string, any>) => {
    const params = {...formData};
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

    const now = getDateObject();

    downloadData(
      params,
      `Space Actions Logs - ${now.format('YYYY-MM-DD HH:mm:ss')}.csv`,
    );
  };

  const onClearForm = () => {
    form.resetFields();
  };

  return (
    <Fragment>
      <AppHeaderButton
        loading={downloading}
        type="default"
        shape="circle"
        size="small"
        onClick={() => setOpen(true)}
        icon={<MdDownload fontSize={20}/>}
      />
      <AppDrawer
        title={formatMessage({id: 'logs.download'})}
        open={open}
        onClose={() => setOpen(false)}
        size={600}
      >
        <DrawerForm form={form} onFinish={onSubmitSuccess}>
          <DrawerBody>
            <AppGridContainer>
              <Col md={12} sm={24}>
                <Item name="from_ts">
                  <AppDateTime
                    placeholder={formatMessage({
                      id: 'downloadLogs.from',
                    })}
                    showTime={{format: 'HH:mm:ss'}}
                    format="DD-MM-YYYY HH:mm:ss"
                  />
                </Item>
              </Col>

              <Col md={12} sm={24}>
                <Item name="to_ts">
                  <AppDateTime
                    placeholder={formatMessage({id: 'downloadLogs.to'})}
                    showTime={{format: 'HH:mm:ss'}}
                    format="DD-MM-YYYY HH:mm:ss"
                  />
                </Item>
              </Col>
            </AppGridContainer>

            <Item name="runs">
              <AppSelect
                placeholder={formatMessage({id: 'downloadLogs.runIds'})}
                mode="multiple"
                optionLabelProp="label"
                optionFilterProp="children"
                allowClear
              >
                {runs?.map((item: RunItem) => (
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
                placeholder={formatMessage({id: 'downloadLogs.agents'})}
                mode="multiple"
                onSearch={onSearch}
                allowClear
              >
                {agents?.data?.map((agent: AgentItem, index) => (
                  <Option key={index} value={agent.handle}>
                    {agent.name}
                  </Option>
                ))}
              </AppSelect>
            </Item>

            <Item name="user_token">
              <AppSelect
                placeholder={formatMessage({id: 'downloadLogs.user'})}
              >
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
                placeholder={formatMessage({
                  id: 'downloadLogs.documentId',
                })}
              />
            </Item>
          </DrawerBody>

          <DrawerFormFooter>
            <Button onClick={onClearForm}>
              {formatMessage({id: 'common.close'})}
            </Button>
            <Button type="primary" htmlType="submit" loading={downloading}>
              {formatMessage({id: 'common.download'})}
            </Button>
          </DrawerFormFooter>
        </DrawerForm>
      </AppDrawer>
    </Fragment>
  );
};

export default ExportTasks;
