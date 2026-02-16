import { useState } from 'react';
import { Button, Form, Modal, Space, Tooltip } from 'antd';
import { MdAdd } from 'react-icons/md';
import { BiBot } from 'react-icons/bi';
import {
  postDataApi,
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppAgentPopover from '@unpod/components/modules/AppAgentPopover';
import { AppInput, AppTextArea } from '@unpod/components/antd';
import AppScheduleInputs from '@unpod/components/modules/AppScheduleInputs';
import { AppHeaderButton } from '@unpod/components/common/AppPageHeader';
import {
  StyledBottomBar,
  StyledContentRoot,
  StyledFormItem,
} from './index.styled';
import type { Document } from '@unpod/constants/types';

const { Item, useForm } = Form;

type AgentPilot = {
  handle?: string;
  name?: string;
  [key: string]: unknown;
};

type AddNewTaskProps = {
  idKey?: string;
  onFinishSchedule?: (data: unknown) => void;
};

const AddNewTask = ({ idKey = 'id', onFinishSchedule }: AddNewTaskProps) => {
  const { setSelectedDocs } = useAppSpaceActionsContext();
  const { selectedDocs, connectorData, currentSpace } = useAppSpaceContext();
  const documents = (connectorData.apiData as Document[]) ?? [];
  const infoViewActionsContext = useInfoViewActionsContext();
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [pilot, setPilot] = useState<AgentPilot | null>(null);
  const [context, setContext] = useState('');
  const [schedule, setSchedule] = useState(false);
  const [repeatType, setRepeatType] = useState('not-repeat');

  const [form] = useForm();

  const onFinish = (values: Record<string, unknown>) => {
    if (pilot) {
      setLoading(true);
      const payload: Record<string, unknown> = {
        ...values,
        pilot: pilot.handle,
      };

      const selectedDocIds = (selectedDocs as Array<string | number>) ?? [];

      if (selectedDocIds.length === 0) {
        payload.documents = [
          {
            count: 1,
            date_ts: 1738127240,
            date: '2025-01-29T05:07:20',
            parent_id: '194b074ec1f58268',
            document_id: '194b074ec1f58268',
            title: values.name,
            description: values.context || 'Write Description',
            user: {
              id: 'google-maps-platform-noreply@google.com',
              name: 'Google Maps Platform',
            },
          },
        ];
      } else {
        payload.documents = documents.filter((item) => {
          const itemId = item[idKey] as string | number;
          return selectedDocIds.includes(itemId);
        });
      }

      postDataApi(
        `tasks/space-task/${currentSpace?.token}/`,
        infoViewActionsContext,
        payload,
      )
        .then((response) => {
          const res = response as { message?: string; data?: unknown };
          if (res.message) infoViewActionsContext.showMessage(res.message);
          onFinishSchedule?.(res.data);
          setOpen(false);
          setPilot(null);
          setContext('');
          setLoading(false);
          setSelectedDocs([]);
          form.resetFields();
        })
        .catch((error) => {
          setLoading(false);
          if (error?.error) {
            infoViewActionsContext.showError(error.error);
          } else {
            infoViewActionsContext.showError(error.message);
          }
        });
    } else {
      infoViewActionsContext.showError('Please select a agent');
    }
  };

  const getContent = () => (
    <StyledContentRoot>
      <Form
        onFinish={onFinish}
        form={form}
        initialValues={{
          repeat_type: 'not-repeat',
          day: 'monday',
        }}
      >
        <StyledFormItem
          name="name"
          rules={[
            {
              required: true,
              message: 'Please enter name',
            },
          ]}
        >
          <AppInput placeholder="Enter Name" variant="borderless" />
        </StyledFormItem>

        <Item
          name="context"
          rules={[
            {
              required: true,
              message: 'Please enter instructions',
            },
          ]}
        >
          <AppTextArea
            placeholder="Enter Instructions"
            variant="borderless"
            autoSize={{ minRows: 3, maxRows: 10 }}
            value={context}
            onChange={(e) => setContext(e.target.value)}
          />
        </Item>

        {schedule && (
          <AppScheduleInputs
            repeatType={repeatType}
            setRepeatType={setRepeatType}
          />
        )}

        <StyledBottomBar>
          <Space align="center" wrap>
            <AppAgentPopover
              pilot={pilot}
              setPilot={setPilot}
              renderChildren={() => (
                <Button type="default" shape="round">
                  <BiBot fontSize={18} />
                  {pilot?.name || 'Select Agent'}
                </Button>
              )}
            />
          </Space>

          <Space align="center" wrap>
            <Button
              type="primary"
              shape="round"
              loading={loading}
              onClick={() => setSchedule(!schedule)}
              ghost
            >
              {schedule ? 'Cancel Schedule' : 'Schedule'}
            </Button>

            <Button
              type="primary"
              shape="round"
              htmlType="submit"
              loading={loading}
            >
              Save
            </Button>
          </Space>
        </StyledBottomBar>
      </Form>
    </StyledContentRoot>
  );

  return (
    <>
      <Tooltip title="Schedule a Task">
        <AppHeaderButton
          type="primary"
          shape="circle"
          size="small"
          icon={<MdAdd fontSize={24} />}
          loading={loading}
          onClick={() => setOpen(true)}
        />
      </Tooltip>
      <Modal
        title={schedule ? 'Schedule a Task' : 'Create a Task'}
        open={open}
        onCancel={() => setOpen(false)}
        footer={null}
        width={650}
        centered
      >
        {getContent()}
      </Modal>
    </>
  );
};

export default AddNewTask;
