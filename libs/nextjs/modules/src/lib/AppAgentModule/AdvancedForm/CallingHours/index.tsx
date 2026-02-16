import { Button, Form, TimePicker, Typography } from 'antd';
import { BsPlusCircleFill, BsTrash } from 'react-icons/bs';
import {
  StyledContainer,
  StyledDayButton,
  StyledDaysContainer,
  StyledTimeRangeRow,
  StyledTimeRangesWrapper,
} from './index.styled';
import dayjs from 'dayjs';
import { useIntl } from 'react-intl';
import { DAYS } from '@unpod/constants/CommonConsts';

const { Paragraph, Title, Text } = Typography;
const { Item, List, useFormInstance, useWatch } = Form;

const CallingHours = () => {
  const form = useFormInstance();
  const selectedDays = useWatch('calling_days', form) || [];
  const { formatMessage } = useIntl();

  const toggleDay = (day: string) => {
    if (selectedDays.includes(day)) {
      form.setFieldValue(
        'calling_days',
        selectedDays.filter((d: string) => d !== day),
      );
    } else {
      form.setFieldValue('calling_days', [...selectedDays, day]);
    }
  };

  return (
    <StyledContainer>
      {/*<Title level={5}>{formatMessage({ id: 'advanced.callingHours' })}</Title>*/}
      <Paragraph type="secondary">
        {formatMessage({ id: 'advanced.callingHoursDesc' })}
      </Paragraph>

      <Title level={5}>{formatMessage({ id: 'advanced.selectDays' })}</Title>

      <Item name="calling_days">
        <StyledDaysContainer>
          {DAYS.map(({ value, label }) => (
            <StyledDayButton
              key={value}
              type={selectedDays.includes(value) ? 'primary' : 'default'}
              onClick={() => toggleDay(value)}
            >
              {formatMessage({ id: label })}
            </StyledDayButton>
          ))}
        </StyledDaysContainer>
      </Item>

      {selectedDays.length > 0 && (
        <>
          <Title level={5}>
            {formatMessage({ id: 'advanced.timeRanges' })}
          </Title>
          <Item
            name="calling_time_ranges"
            dependencies={['calling_days']}
            rules={[
              {
                validator: async (_, ranges) => {
                  if (
                    selectedDays.length > 0 &&
                    (!ranges || ranges.length === 0)
                  ) {
                    return Promise.reject(
                      new Error(
                        formatMessage({ id: 'validation.minOneSlotError' }),
                      ),
                    );
                  }
                  return Promise.resolve();
                },
              },
            ]}
          >
            <List name="calling_time_ranges">
              {(fields, { add, remove }) => (
                <StyledTimeRangesWrapper>
                  {fields.map(({ key, name, ...restField }) => (
                    <StyledTimeRangeRow key={key}>
                      <Item
                        {...restField}
                        name={[name, 'start']}
                        rules={[{ required: true, message: '' }]}
                        initialValue={dayjs('08:00 AM', 'hh:mm A')}
                        noStyle
                      >
                        <TimePicker
                          placeholder={formatMessage({
                            id: 'advanced.startTime',
                          })}
                          format="hh:mm A"
                          size="middle"
                        />
                      </Item>

                      <Text style={{ wordBreak: 'normal' }}>
                        {formatMessage({ id: 'advanced.to' })}
                      </Text>

                      <Item
                        {...restField}
                        name={[name, 'end']}
                        rules={[{ required: true, message: '' }]}
                        initialValue={dayjs('08:00 PM', 'hh:mm A')}
                        noStyle
                      >
                        <TimePicker
                          placeholder={formatMessage({
                            id: 'advanced.endTime',
                          })}
                          format="hh:mm A"
                          size="middle"
                        />
                      </Item>

                      {fields.length > 1 && (
                        <Button
                          type="link"
                          size="small"
                          onClick={() => remove(name)}
                          danger
                          ghost
                        >
                          <BsTrash size={16} />
                        </Button>
                      )}
                    </StyledTimeRangeRow>
                  ))}

                  {fields.length < 5 && (
                    <Button
                      type="link"
                      size="small"
                      icon={<BsPlusCircleFill size={16} />}
                      onClick={add}
                    >
                      {formatMessage({ id: 'advanced.addRange' })}
                    </Button>
                  )}
                </StyledTimeRangesWrapper>
              )}
            </List>
          </Item>
        </>
      )}
    </StyledContainer>
  );
};

export default CallingHours;
