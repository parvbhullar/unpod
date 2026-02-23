'use client';
import {useState} from 'react';

import {Col, Form, Row, Select} from 'antd';
import dayjs from 'dayjs';
import AppSelect from '../../antd/AppSelect';
import AppDate from '../../antd/AppDate';
import AppTime from '../../antd/AppTime';
import {getScheduleOptions} from '@unpod/helpers/DateHelper';
import {useIntl} from 'react-intl';

const {Option} = Select;
const {Item} = Form;
const customScheduleOptions = getScheduleOptions();

const AppScheduleInputs = ({form}: { form: any }) => {
  const {formatMessage} = useIntl();
  const [repeatType, setRepeatType] = useState('not-repeat');

  const repeatOptions = [
    {label: 'schedule.notRepeat', value: 'not-repeat', mode: 'date'},
    {label: 'schedule.daily', value: 'daily', mode: 'date'},
    {label: 'schedule.weekly', value: 'weekly', mode: 'date'},
    {label: 'schedule.monthly', value: 'monthly', mode: 'date'},
    {label: 'schedule.annually', value: 'annually', mode: 'month'},
    {label: 'schedule.custom', value: 'custom', mode: 'date'},
  ];

  const weekDays = [
    {label: 'week.sunday', value: 'sunday'},
    {label: 'week.monday', value: 'monday'},
    {label: 'week.tuesday', value: 'tuesday'},
    {label: 'week.wednesday', value: 'wednesday'},
    {label: 'week.thursday', value: 'thursday'},
    {label: 'week.friday', value: 'friday'},
    {label: 'week.saturday', value: 'saturday'},
  ];

  const onRepeatTypeChange = (
    value: string | number | object | unknown[] | null,
  ) => {
    const selectedValue = typeof value === 'string' ? value : '';
    const selected =
      repeatOptions.find((option) => option.value === selectedValue) ||
      repeatOptions[0];
    setRepeatType(selected.value);
  };

  const onChangeCustom = (
    value: string | number | object | unknown[] | null,
  ) => {
    const selectedValue = typeof value === 'string' ? value : '';
    if (selectedValue) {
      const selected = customScheduleOptions.find(
        (option: any) => option.date === selectedValue,
      );

      if (selected) {
        form.setFieldsValue({
          date: dayjs(selected.date, 'YYYY-MM-DD'),
          time: dayjs(selected.time, 'HH:mm'),
        });
      }
    }
  };

  return (
    <Row gutter={12}>
      <Col sm={24} md={8}>
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
            placeholder={formatMessage({id: 'schedule.repeatType'})}
            onChange={onRepeatTypeChange}
          >
            {repeatOptions.map((option) => (
              <Option key={option.value} value={option.value}>
                {formatMessage({id: option.label})}
              </Option>
            ))}
          </AppSelect>
        </Item>
      </Col>

      {repeatType === 'custom' && (
        <Col sm={24} md={16}>
          <Row>
            <Col sm={24} md={18}>
              <Item>
                <AppSelect
                  placeholder={formatMessage({id: 'schedule.customDateTime'})}
                  onChange={onChangeCustom}
                  allowClear
                >
                  {customScheduleOptions.map((option) => (
                    <Option key={option.key} value={option.key}>
                      {option.title}
                    </Option>
                  ))}
                </AppSelect>
              </Item>
            </Col>
          </Row>
        </Col>
      )}

      {repeatType === 'weekly' && (
        <Col sm={24} md={8}>
          <Item
            name="day"
            rules={[
              {
                required: true,
                message: formatMessage({id: 'schedule.selectDay'}),
              },
            ]}
          >
            <AppSelect placeholder={formatMessage({id: 'schedule.day'})}>
              {weekDays.map((option) => (
                <Option key={option.value} value={option.value}>
                  {formatMessage({id: option.label})}
                </Option>
              ))}
            </AppSelect>
          </Item>
        </Col>
      )}

      {(repeatType === 'monthly' ||
        repeatType === 'annually' ||
        repeatType === 'custom') && (
        <Col sm={24} md={8}>
          <Item
            name="date"
            rules={[
              {
                required: true,
                message: formatMessage({id: 'schedule.selectDate'}),
              },
            ]}
          >
            <AppDate
              placeholder={formatMessage({id: 'schedule.date'})}
              picker={repeatOptions.find((r) => r.value === repeatType)?.mode}
            />
          </Item>
        </Col>
      )}

      {repeatType !== 'not-repeat' && (
        <Col sm={24} md={8}>
          <Item
            name="time"
            rules={[
              {
                required: true,
                message: formatMessage({id: 'schedule.selectTime'}),
              },
            ]}
          >
            <AppTime
              placeholder={formatMessage({id: 'schedule.time'})}
              format="HH:mm"
              defaultOpenValue={dayjs('09:00:00', 'HH:mm:ss')}
            />
          </Item>
        </Col>
      )}
    </Row>
  );
};

export default AppScheduleInputs;
