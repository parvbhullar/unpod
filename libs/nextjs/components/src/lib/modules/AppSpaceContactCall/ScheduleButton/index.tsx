import React, {Fragment, useMemo, useState} from 'react';

import {Button, Calendar, type CalendarProps, Form, Modal, Select, Space, theme, Typography,} from 'antd';
import {MdArrowDropDown, MdArrowDropUp, MdCalendarMonth, MdScheduleSend,} from 'react-icons/md';
import {getDateObject} from '@unpod/helpers/DateHelper';
import type {Dayjs} from 'dayjs';
import AppDate from '../../../antd/AppDate';
import AppTime from '../../../antd/AppTime';
import AppSelect from '../../../antd/AppSelect';
import {
  StyledCalendarRoot,
  StyledCalendarWrapper,
  StyledDropdownButton,
  StyledInputsWrapper,
  StyledMenu,
  StyledMenuItem,
  StyledModalContainer,
} from './index.styled';
import {useIntl} from 'react-intl';

const {Option} = Select;
const {Text} = Typography;
const {Item, useForm} = Form;

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

const repeatOptions: RepeatOption[] = [
  {label: 'schedule.once', value: 'once', mode: 'date', calendar: 'month'},
  {label: 'schedule.daily', value: 'daily', mode: 'date', calendar: 'month'},
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

const defaultOption: RepeatOption = repeatOptions[0];

type ScheduleItem = {
  label: string;
  time: string;
  timeIn24Hours: string;
  key: string;
};

type RepeatOption = {
  label: string;
  value: string;
  mode: 'date' | 'month';
  calendar: 'month';
};

type ScheduleValues = {
  date: Dayjs;
  time: Dayjs;
  repeat_type: string;
  day?: string;
};

type SchedulePayload = {
  date: string;
  time: string;
  repeat_type: string;
  day?: string;
};

type ScheduleButtonProps = {
  pilot?: unknown;
  onSchedule?: (values: SchedulePayload) => void;
  loading?: boolean;
};

const ScheduleButton = ({
                          pilot,
                          onSchedule,
                          loading,
                          ...restProps
                        }: ScheduleButtonProps) => {
  const {token} = theme.useToken();
  const [form] = useForm();
  const {formatMessage} = useIntl();

  const wrapperStyle = {
    border: `1px solid ${token.colorBorderSecondary}`,
    borderRadius: token.borderRadiusLG,
  };

  const [openSchedule, setOpenSchedule] = useState(false);
  const [calendarMode, setCalendarMode] =
    useState<CalendarProps<Dayjs>['mode']>('month');
  const [repeatType, setRepeatType] = useState<RepeatOption>(defaultOption);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [openDateTime, setOpenDateTime] = useState(false);
  const [calendarDate, setCalendarDate] = useState<Dayjs | undefined>(
    undefined,
  );

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

  const handleMenuClick = (item: { key?: string }) => {
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

  const onRepeatTypeChange = (
    value: string | number | object | unknown[] | null,
  ) => {
    const selectedValue = typeof value === 'string' ? value : '';
    const selected = repeatOptions.find(
      (option) => option.value === selectedValue,
    );
    setRepeatType(selected || defaultOption);
  };

  const onPanelChange = (date: Dayjs, mode: CalendarProps<Dayjs>['mode']) => {
    setCalendarMode(mode);
    form.setFieldValue('date', date);
    setCalendarDate(date);
  };

  const onDateSelect = (date: Dayjs) => {
    form.setFieldValue('date', date);
    setCalendarDate(date);
  };

  const onDatePickerChange = (date: Dayjs | null) => {
    setCalendarDate(date || undefined);
  };

  const onFinishSchedule = (values: ScheduleValues) => {
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
      <StyledDropdownButton
        type="primary"
        trigger={['click']}
        disabled={!pilot}
        menu={{
          items: [
            {
              label: formatMessage({id: 'schedule.title'}),
              key: 'schedule-ask',
              icon: (
                <span className="anticon">
                  <MdScheduleSend fontSize={16}/>
                </span>
              ),
            },
          ],
          onClick: handleMenuClick,
        }}
        onOpenChange={setOpenSchedule}
        icon={
          openSchedule ? (
            <MdArrowDropUp fontSize={18}/>
          ) : (
            <MdArrowDropDown fontSize={18}/>
          )
        }
        buttonsRender={([leftButton, rightButton]) => [
          React.cloneElement(
            leftButton as React.ReactElement<any>,
            {
              shape: 'round',
              htmlType: 'submit',
              loading: loading,
            } as any,
          ),
          React.cloneElement(
            rightButton as React.ReactElement<any>,
            {
              shape: 'round',
              loading: loading,
            } as any,
          ),
        ]}
        {...restProps}
      >
        Submit
      </StyledDropdownButton>

      <Modal
        title={
          openDateTime
            ? formatMessage({id: 'schedule.pickDateTime'})
            : formatMessage({id: 'schedule.title'})
        }
        open={isModalOpen}
        onCancel={handleCancel}
        width={openDateTime ? 650 : 350}
        styles={{
          body: {padding: 0},
          header: {padding: '20px 16px 0 16px'},
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
                    value={calendarDate}
                    mode={calendarMode}
                  />
                </StyledCalendarWrapper>

                <StyledInputsWrapper>
                  <Item
                    name="repeat_type"
                    rules={[
                      {
                        required: true,
                        message: formatMessage({id: 'schedule.selectOption'}),
                      },
                    ]}
                  >
                    <AppSelect
                      placeholder={formatMessage({
                        id: 'schedule.repeatType',
                      })}
                      defaultValue={defaultOption.value}
                      onChange={onRepeatTypeChange}
                    >
                      {repeatOptions.map((option) => (
                        <Option key={option.value} value={option.value}>
                          {formatMessage({id: option.label})}
                        </Option>
                      ))}
                    </AppSelect>
                  </Item>

                  <Item
                    name="date"
                    rules={[
                      {
                        required: true,
                        message: formatMessage({
                          id: 'schedule.selectDate',
                        }),
                      },
                    ]}
                  >
                    <AppDate
                      placeholder={formatMessage({
                        id: 'schedule.date',
                      })}
                      onChange={onDatePickerChange}
                      picker={repeatType.mode}
                    />
                  </Item>

                  <Item
                    name="time"
                    rules={[
                      {
                        required: true,
                        message: formatMessage({
                          id: 'schedule.selectDate',
                        }),
                      },
                    ]}
                  >
                    <AppTime
                      placeholder={formatMessage({
                        id: 'schedule.time',
                      })}
                      format="HH:mm"
                    />
                  </Item>

                  <Button type="primary" shape="round" htmlType="submit">
                    {formatMessage({
                      id: 'schedule.title',
                    })}
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
                    <Text>{formatMessage({id: item.label})}</Text>
                    <Text>{item.time}</Text>
                  </StyledMenuItem>
                ))}
                <StyledMenuItem onClick={() => setOpenDateTime(true)}>
                  <Space>
                    <MdCalendarMonth fontSize={18}/>
                    <Text>
                      {formatMessage({id: 'schedule.pickDateTime'})}
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

export default ScheduleButton;
