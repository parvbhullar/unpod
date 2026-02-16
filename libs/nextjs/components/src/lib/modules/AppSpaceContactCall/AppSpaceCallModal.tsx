import { useEffect, useState } from 'react';
import { Button, Form, Modal, Space } from 'antd';
import {
  StyledBottomBar,
  StyledContentRoot,
  StyledInput,
} from './index.styled';
import AppScheduleInputs from '../AppScheduleInputs';
import AppAgentPopover from '../AppAgentPopover';
import { BiBot } from 'react-icons/bi';
import {
  postDataApi,
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import {
  getBrowserTimezone,
  getFormattedDate,
  getUtcTimestamp,
} from '@unpod/helpers/DateHelper';
import { useIntl } from 'react-intl';

const { Item, useForm } = Form;
type AppSpaceCallModalProps = {
  open: boolean;
  idKey: string;
  onFinishSchedule?: (data: any) => void;
  setOpen: (open: boolean) => void;
  filters?: any;
  from?: string;};

const AppSpaceCallModal = ({
  open,
  idKey,
  onFinishSchedule,
  setOpen,
  filters,
  from = 'doc',
}: AppSpaceCallModalProps) => {
  const { setSelectedDocs } = useAppSpaceActionsContext();
  const { selectedDocs, connectorData, currentSpace, activeCall } =
    useAppSpaceContext();
  const { formatMessage } = useIntl();

  const infoViewActionsContext = useInfoViewActionsContext();
  const [loading, setLoading] = useState(false);

  const [schedule, setSchedule] = useState(false);

  const [repeatType, setRepeatType] = useState('now');

  const [pilot, setPilot] = useState<any | null>(
    activeCall?.assignee ? { name: activeCall.assignee } : null,
  );
  const [form] = useForm();

  useEffect(() => {
    const firstPilot = currentSpace?.pilots?.[0];
    if (!activeCall?.assignee && firstPilot) {
      setPilot(firstPilot);
    }
  }, [currentSpace, activeCall]);

  const getDocumentPayload = (data: any) => {
    if (!data) return null;
    if (data?.status === 'in_progress' && data?.input?.contact_number) {
      return {
        contact_number: data.input.contact_number,
        name: data?.input?.name?.startsWith('sip') ? '' : data?.input?.name,
        documents: data?.input?.documents || [],
      };
    }
    if (data?.status === 'completed') {
      // If call type is inbound, use output.customer
      if (data?.output?.call_type === 'inbound' && data?.output?.customer) {
        return {
          contact_number: data.output.customer,
          name: data?.input?.name?.startsWith('sip') ? '' : data?.input?.name,
          documents: data?.input?.documents || [],
        };
      }
      // If call type is inbound, use output.customer
      if (data?.output?.call_type === 'outbound') {
        return {
          contact_number: data.input.contact_number
            ? data.input.contact_number
            : data.output.customer,
          name: data?.input?.name?.startsWith('sip') ? '' : data?.input?.name,
          documents: data?.input?.documents || [],
        };
      }
    }
    return {
      contact_number: data?.input?.contact_number,
      name: data?.input?.name?.startsWith('sip') ? '' : data?.input?.name,
    };
  };
  const onFinish = (values: any) => {
    form
      .validateFields()
      .then(() => {
        if (pilot) {
          setLoading(true);

          const payload: Record<string, any> = { pilot: pilot.handle };
          if (from === 'call' && activeCall) {
            payload.documents = [{ document_id: activeCall.ref_id }];
          }
          if (from === 'doc') {
            if (filters) {
              payload.filters = {
                ...filters,
                from_ts: filters?.from_ts
                  ? getUtcTimestamp(filters?.from_ts)
                  : '',
                to_ts: filters?.to_ts ? getUtcTimestamp(filters?.to_ts) : '',
              };
            }
            if (filters?.fetch_all !== '1') {
              payload.documents = (connectorData.apiData || []).filter(
                (item: any) => selectedDocs.includes(item[idKey]),
              );
            }
          } else {
            payload.documents = [getDocumentPayload(activeCall)];
          }
          payload.context = values.context;
          payload.schedule =
            repeatType === 'custom'
              ? {
                  type: repeatType,
                  calling_date: getFormattedDate(values.date, 'YYYY-MM-DD'),
                  calling_time:
                    getFormattedDate(values.time, 'HH:mm:ss') +
                    getBrowserTimezone(),
                  day: values.day,
                }
              : { type: repeatType };

          postDataApi(
            `tasks/space-task/${currentSpace?.token}/`,
            infoViewActionsContext,
            payload,
          )
            .then((response: any) => {
              infoViewActionsContext.showMessage(response.message);
              onFinishSchedule?.(response.data);
              setOpen(false);
              setPilot(null);
              setLoading(false);
              setSelectedDocs?.([]);
              form.resetFields();
            })
            .catch((error: any) => {
              setLoading(false);
              if (error?.error) {
                infoViewActionsContext.showError(error.error);
              } else {
                infoViewActionsContext.showError(error.message);
              }
            });
        } else {
          infoViewActionsContext.showError(
            formatMessage({ id: 'validation.selectAgentError' }),
          );
        }
      })
      .catch(() => {
        infoViewActionsContext.showError(
          formatMessage({ id: 'validation.instructionsMessage' }),
        );
      });
  };
  return (
    <Modal
      title={formatMessage({ id: 'appSpaceCallModal.title' })}
      open={open}
      onCancel={() => setOpen(false)}
      footer={null}
      width={650}
      centered
      zIndex={1001}
    >
      <StyledContentRoot>
        <Form
          scrollToFirstError={false}
          preserve={false}
          onFinish={onFinish}
          form={form}
          initialValues={{
            repeat_type: 'now',
            day: 'monday',
          }}
        >
          <Item
            name="context"
            initialValue={formatMessage({ id: 'instructions.defaultMessage' })}
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'validation.instructionsMessage',
                }),
              },
            ]}
          >
            <StyledInput
              placeholder={formatMessage({
                id: 'appSpaceCallModal.instructionsPlaceholder',
              })}
              variant="borderless"
              autoSize={{ minRows: 2, maxRows: 10 }}
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
                type="Voice"
                renderChildren={() => (
                  <Button type="default" shape="round">
                    <BiBot fontSize={18} />
                    {pilot?.name ||
                      formatMessage({ id: 'appSpaceCallModal.selectAgent' })}
                  </Button>
                )}
              />
            </Space>

            <Space size="small" align="center" wrap>
              <Button
                type="primary"
                shape="round"
                onClick={() => setSchedule(!schedule)}
                ghost
              >
                {schedule
                  ? formatMessage({ id: 'appSpaceCallModal.cancelSchedule' })
                  : formatMessage({ id: 'appSpaceCallModal.schedule' })}
              </Button>

              <Button
                type="primary"
                shape="round"
                htmlType="submit"
                loading={loading}
              >
                {formatMessage({ id: 'common.submit' })}
              </Button>
            </Space>
          </StyledBottomBar>
        </Form>
      </StyledContentRoot>
    </Modal>
  );
};

export default AppSpaceCallModal;
