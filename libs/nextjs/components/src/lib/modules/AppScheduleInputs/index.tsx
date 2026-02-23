'use client';

import {Form, Radio, Space, Typography} from 'antd';
import dayjs from 'dayjs';
import AppDate from '../../antd/AppDate';
import AppTime from '../../antd/AppTime';
import {useIntl} from 'react-intl';

const {Item, useWatch, useFormInstance} = Form;
const {Text} = Typography;

const AppScheduleInputs = ({
                             repeatType,
                             setRepeatType,
                           }: {
  repeatType: string;
  setRepeatType: (value: string) => void;
}) => {
  const {formatMessage} = useIntl();
  const form = useFormInstance();
  const repeatTypeValue = useWatch('repeat_type', form);

  return (
    <Item
      name="repeat_type"
      rules={[
        {
          required: true,
          message: formatMessage({id: 'schedule.schedulingOption'}),
        },
      ]}
      noStyle={repeatTypeValue === 'custom' && true}
    >
      <Radio.Group
        onChange={(e) => setRepeatType(e.target.value)}
        value={repeatType}
        style={{width: '100%'}}
      >
        <Space orientation="vertical" style={{width: '100%'}}>
          <Radio value="now">{formatMessage({id: 'schedule.now'})}</Radio>
          {repeatType === 'now' && (
            <Text type="secondary">
              {formatMessage({id: 'schedule.nowInfo'})}
            </Text>
          )}

          <Radio value="auto">{formatMessage({id: 'schedule.auto'})}</Radio>
          {repeatType === 'auto' && (
            <Text type="secondary">
              {formatMessage({id: 'schedule.autoInfo'})}
            </Text>
          )}

          <Radio value="custom">
            {formatMessage({id: 'schedule.customSchedule'})}
          </Radio>

          {repeatType === 'custom' && (
            <Space orientation="vertical" size="small" style={{width: '100%'}}>
              <Text type="secondary">
                {formatMessage({id: 'schedule.customInfo'})}
              </Text>

              <Space size="middle" wrap align="start">
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
                    format="MM/DD/YYYY"
                    placeholder={formatMessage({id: 'schedule.date'})}
                    picker="date"
                    disabledDate={(current: any) =>
                      current && current < dayjs().startOf('day')
                    }
                  />
                </Item>

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
                    format="hh:mm A"
                    disabledTime={(date: any) => {
                      if (!date) return {};
                      const now = dayjs();
                      if (date.isSame(now, 'day')) {
                        return {
                          disabledHours: () =>
                            Array.from({length: now.hour()}, (_, i) => i),
                          disabledMinutes: (hour: number) =>
                            hour === now.hour()
                              ? Array.from(
                                {length: now.minute()},
                                (_, i) => i,
                              )
                              : [],
                        };
                      }
                      return {};
                    }}
                  />
                </Item>
              </Space>
            </Space>
          )}
        </Space>
      </Radio.Group>
    </Item>
  );
};

export default AppScheduleInputs;
