import { cloneElement, Fragment, useMemo, useState } from 'react';
import type { Dayjs } from 'dayjs';

import {
  Button,
  Calendar,
  Form,
  Modal,
  Select,
  Space,
  theme,
  Typography,
} from 'antd';
import {
  MdArrowDropDown,
  MdArrowDropUp,
  MdArrowForward,
  MdCalendarMonth,
  MdScheduleSend,
} from 'react-icons/md';
import { useAuthContext } from '@unpod/providers';
import AppDate from '../../../antd/AppDate';
import AppTime from '../../../antd/AppTime';
import { getDateObject } from '@unpod/helpers/DateHelper';
import AppSelect from '../../../antd/AppSelect';
import {
  StyledButton,
  StyledCalendarRoot,
  StyledCalendarWrapper,
  StyledDropdownButton,
  StyledInputsWrapper,
  StyledMenu,
  StyledMenuItem,
  StyledModalContainer,
} from './index.styled';
import { useIntl } from 'react-intl';

const { Option } = Select;
const { Text } = Typography;
const { Item, useForm } = Form;

type ScheduleItem = {
  label: string;
  time: string;
  timeIn24Hours: string;
  key: string;
};

const items: ScheduleItem[] = [
  {
    label: 'schedule.tomorrowMorning',
    time: '8:00 AM',
    timeIn24Hours: '08:00:00',
    key: 'tomorrow-morning',
  },
  {
    label: 'schedule.tomorrowAfternoon',
    time: '1:00 PM',
    timeIn24Hours: '13:00:00',
    key: 'tomorrow-afternoon',
  },
  {
    label: 'schedule.tomorrowEvening',
    time: '6:00 PM',
    timeIn24Hours: '18:00:00',
    key: 'tomorrow-evening',
  },
];

type RepeatOption = {
  label: string;
  value: string;
  mode: 'date' | 'month';
  calendar: 'month';
};

const repeatOptions: RepeatOption[] = [
  { label: 'schedule.once', value: 'once', mode: 'date', calendar: 'month' },
  { label: 'schedule.daily', value: 'daily', mode: 'date', calendar: 'month' },
  {
    label: 'schedule.weekly',
    value: 'weekly',
    mode: 'date',
    calendar: 'month',
  },
  {
    label: 'schedule.quarterly',
    value: 'quarterly',
    mode: 'date',
    calendar: 'month',
  },
  {
    label: 'schedule.monthly',
    value: 'monthly',
    mode: 'date',
    calendar: 'month',
  },
  {
    label: 'schedule.yearly',
    value: 'yearly',
    mode: 'month',
    calendar: 'month',
  },
];

const defaultOption = repeatOptions[0];

type SendButtonProps = {
  query?: string | null;
  attachments?: any[];
  onSchedule?: (values: Record<string, any>) => void;};

const SendButton = ({
  query,
  attachments = [],
  onSchedule,
}: SendButtonProps) => {
  const { isAuthenticated } = useAuthContext();
  const { token } = theme.useToken();
  const [form] = useForm();

  const wrapperStyle = {
    border: `1px solid ${token.colorBorderSecondary}`,
    borderRadius: token.borderRadiusLG,
  };

  const [openSchedule, setOpenSchedule] = useState(false);
  const [calendarMode, setCalendarMode] = useState<'month' | 'year'>('month');
  const [repeatType, setRepeatType] = useState<RepeatOption>(defaultOption);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [openDateTime, setOpenDateTime] = useState(false);
  const [calendarDate, setCalendarDate] = useState<Dayjs | null>(null);
  const { formatMessage } = useIntl();

  const today = useMemo(() => {
    const currentDateTime = getDateObject();
    setCalendarDate(currentDateTime);

    return currentDateTime;
  }, []);

  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    setTimeout(() => {
      setOpenDateTime(false);
    }, 500);
  };

  const handleMenuClick = (item: { key: string }) => {
    if (item.key === 'schedule-ask') {
      showModal();
    }
  };

  const onScheduleItemClick = (item: ScheduleItem) => {
    const tomorrow = today.add(1, 'days');
    const tomorrowDateTime = getDateObject(
      `${tomorrow.format('YYYY-MM-DD')} ${item.timeIn24Hours}`,
      'YYYY-MM-DD HH:mm:ss',
    );
    const tomorrowUtc = (tomorrowDateTime as any).utc?.() || tomorrowDateTime;

    onSchedule?.({
      date: tomorrowUtc.format('YYYY-MM-DD'),
      time: tomorrowUtc.format('HH:mm'),
      repeat_type: 'once',
    });

    handleCancel();
  };

  const onRepeatTypeChange = (value: string) => {
    const selected =
      repeatOptions.find((option) => option.value === value) || defaultOption;
    setRepeatType(selected);
  };

  const onPanelChange = (date: Dayjs, mode: 'month' | 'year') => {
    setCalendarMode(mode);
    form.setFieldValue('date', date);
    setCalendarDate(date);
  };

  const onDateSelect = (date: Dayjs) => {
    form.setFieldValue('date', date);
    setCalendarDate(date);
  };

  const onDatePickerChange = (date: Dayjs | null) => {
    setCalendarDate(date);
  };

  const onFinishSchedule = (values: any) => {
    const dateTime = getDateObject(
      `${values.date.format('YYYY-MM-DD')} ${values.time.format('HH:mm:ss')}`,
      'YYYY-MM-DD HH:mm:ss',
    );
    const utcDateTime = (dateTime as any).utc?.() || dateTime;

    onSchedule?.({
      ...values,
      date: utcDateTime.format('YYYY-MM-DD'),
      time: utcDateTime.format('HH:mm'),
    });

    form.resetFields();
    handleCancel();
  };

  return (
    <Fragment>
      {isAuthenticated && (query || attachments.length > 0) ? (
        <StyledDropdownButton
          type="primary"
          trigger={['click']}
          menu={{
            items: [
              {
                label: formatMessage({ id: 'schedule.title' }),
                key: 'schedule-ask',
                icon: (
                  <span className="anticon">
                    <MdScheduleSend fontSize={16} />
                  </span>
                ),
              },
            ],
            onClick: handleMenuClick,
          }}
          onOpenChange={setOpenSchedule}
          icon={
            openSchedule ? (
              <MdArrowDropUp fontSize={18} />
            ) : (
              <MdArrowDropDown fontSize={18} />
            )
          }
          buttonsRender={([leftButton, rightButton]) => [
            cloneElement(leftButton as any, {
              shape: 'round',
              htmlType: 'submit',
            }),
            cloneElement(rightButton as any, {
              shape: 'round',
            }),
          ]}
        >
          {formatMessage({ id: 'common.submit' })}
        </StyledDropdownButton>
      ) : (
        <StyledButton type="primary" shape="round" htmlType="submit">
          {formatMessage({ id: 'common.submit' })}
          <MdArrowForward fontSize={18} />
        </StyledButton>
      )}

      <Modal
        title={
          openDateTime
            ? formatMessage({ id: 'schedule.pickDateTime' })
            : formatMessage({ id: 'schedule.title' })
        }
        open={isModalOpen}
        onCancel={handleCancel}
        width={openDateTime ? 650 : 350}
        styles={{
          body: { padding: 0 },
          header: { padding: '20px 16px 0 16px' },
        }}
        footer={null}
        centered
      >
        <Form
          form={form}
          onFinish={onFinishSchedule}
          initialValues={{
            repeat_type: defaultOption.value,
            date: today,
            time: today,
          }}
        >
          <StyledModalContainer>
            {openDateTime ? (
              <StyledCalendarRoot>
                <StyledCalendarWrapper style={wrapperStyle}>
                  <Calendar
                    fullscreen={false}
                    onPanelChange={onPanelChange}
                    onSelect={onDateSelect}
                    value={calendarDate || undefined}
                    mode={calendarMode}
                  />
                </StyledCalendarWrapper>

                <StyledInputsWrapper>
                  <Item
                    name="repeat_type"
                    rules={[
                      {
                        required: true,
                        message: formatMessage({ id: 'schedule.selectOption' }),
                      },
                    ]}
                  >
                    <AppSelect
                      placeholder={formatMessage({ id: 'schedule.repeatType' })}
                      defaultValue={defaultOption.value}
                      onChange={(value) => onRepeatTypeChange(String(value))}
                    >
                      {repeatOptions.map((option) => (
                        <Option key={option.value} value={option.value}>
                          {formatMessage({ id: option.label })}
                        </Option>
                      ))}
                    </AppSelect>
                  </Item>

                  <Item
                    name="date"
                    rules={[
                      {
                        required: true,
                        message: formatMessage({ id: 'schedule.selectDate' }),
                      },
                    ]}
                  >
                    <AppDate
                      placeholder={formatMessage({ id: 'schedule.date' })}
                      onChange={onDatePickerChange}
                      picker={repeatType.mode}
                    />
                  </Item>

                  <Item
                    name="time"
                    rules={[
                      {
                        required: true,
                        message: formatMessage({ id: 'schedule.selectTime' }),
                      },
                    ]}
                  >
                    <AppTime
                      placeholder={formatMessage({ id: 'schedule.time' })}
                      format="HH:mm"
                    />
                  </Item>

                  <Button type="primary" shape="round" htmlType="submit">
                    {formatMessage({ id: 'schedule.title' })}
                  </Button>
                </StyledInputsWrapper>
              </StyledCalendarRoot>
            ) : (
              <StyledMenu>
                {items.map((item) => (
                  <StyledMenuItem
                    key={item.key}
                    onClick={() => onScheduleItemClick(item)}
                  >
                    <Text>{formatMessage({ id: item.label })}</Text>
                    <Text>{item.time}</Text>
                  </StyledMenuItem>
                ))}
                <StyledMenuItem onClick={() => setOpenDateTime(true)}>
                  <Space>
                    <MdCalendarMonth fontSize={18} />
                    <Text>
                      {formatMessage({ id: 'schedule.pickDateTime' })}
                    </Text>
                  </Space>
                </StyledMenuItem>
              </StyledMenu>
            )}
          </StyledModalContainer>
        </Form>
      </Modal>
    </Fragment>
  );
};

export default SendButton;
