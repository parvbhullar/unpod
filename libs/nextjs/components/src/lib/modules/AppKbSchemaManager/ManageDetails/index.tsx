'use client';
import { CSSProperties, useEffect, useState } from 'react';
import { Button, Form, Modal, Row, Select } from 'antd';
import { getMachineName } from '@unpod/helpers/StringHelper';
import {
  AppDate,
  AppDateTime,
  AppInput,
  AppSelect,
  AppTextArea,
  AppTime,
} from '../../../antd';
import { StyledChoicesContainer } from './index.styled';
import { REQUIRED_CONTACT_FIELDS } from '@unpod/constants';
import { useIntl } from 'react-intl';

const { Item } = Form;
const { Option } = Select;

const DEFAULT_VALUE_PLACEHOLDER = 'schema.enterDefaultValue';

type SchemaInput = {
  name?: string;
  title?: string;
  type?: string;
  choices?: string[];
  [key: string]: any;
};

type ManageDetailsProps = {
  selectedItem?: SchemaInput | null;
  onFinish: (values: any) => void;
  initialValues?: any;
  contentType?: string;
  overflowY?: CSSProperties['overflowY'];
  [key: string]: unknown;
};

const ManageDetails = ({
  selectedItem,
  onFinish,
  initialValues,
  contentType,
  overflowY = 'hidden',
  ...restProps
}: ManageDetailsProps) => {
  const [choices, setChoices] = useState<string[]>([]);
  const { formatMessage } = useIntl();

  useEffect(() => {
    if (selectedItem?.choices) {
      setChoices(selectedItem.choices);
    }
  }, [selectedItem]);

  const handleChoicesChange = (value: any) => {
    setChoices(Array.isArray(value) ? value : []);
  };
  return (
    <Modal
      title={formatMessage({ id: 'schema.manageDetails' })}
      footer={null}
      destroyOnHidden
      centered
      {...restProps}
      style={{ overflowY: overflowY }}
    >
      <StyledChoicesContainer>
        <Form
          layout="vertical"
          initialValues={initialValues || { choices: [] }}
          onFinish={onFinish}
        >
          <Item
            name="title"
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'validation.fieldRequired' }),
              },
              (form) => ({
                validator(_, title) {
                  if (title && !selectedItem?.name) {
                    form.setFieldsValue({
                      name: getMachineName(title),
                    });
                  }
                  return Promise.resolve();
                },
              }),
            ]}
          >
            <AppInput
              placeholder={formatMessage({ id: 'schema.enterFieldTitle' })}
              asterisk
            />
          </Item>

          {!(
            contentType === 'contact' &&
            REQUIRED_CONTACT_FIELDS.includes(selectedItem?.name as any)
          ) && (
            <Item
              name="name"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.fieldRequired' }),
                },
                (form) => ({
                  validator(_, name) {
                    if (name) {
                      form.setFieldsValue({
                        name: getMachineName(name),
                      });
                    }
                    return Promise.resolve();
                  },
                }),
              ]}
            >
              <AppInput
                placeholder={formatMessage({ id: 'schema.enterFieldTitle' })}
                asterisk
              />
            </Item>
          )}

          {(selectedItem?.type === 'select' ||
            selectedItem?.type === 'multi-select' ||
            selectedItem?.type === 'checkboxes') && (
            <Item
              name="choices"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.fieldRequired' }),
                },
              ]}
            >
              <AppSelect
                placeholder={formatMessage({ id: 'form.enterChoices' })}
                onChange={handleChoicesChange}
                mode="tags"
                asterisk
              />
            </Item>
          )}

          <Item
            name="defaultValue"
            rules={[
              {
                required: false,
                message: formatMessage({ id: 'validation.fieldRequired' }),
              },
            ]}
          >
            {selectedItem?.type === 'select' ||
            selectedItem?.type === 'multi-select' ||
            selectedItem?.type === 'checkboxes' ? (
              <AppSelect
                placeholder={formatMessage({ id: DEFAULT_VALUE_PLACEHOLDER })}
                mode={
                  selectedItem?.type === 'multi-select' ||
                  selectedItem?.type === 'checkboxes'
                    ? 'multiple'
                    : ''
                }
              >
                {choices.map((choice, index) => (
                  <Option key={index} value={choice}>
                    {choice}
                  </Option>
                ))}
              </AppSelect>
            ) : selectedItem?.type === 'date' ? (
              <AppDate
                placeholder={formatMessage({ id: DEFAULT_VALUE_PLACEHOLDER })}
              />
            ) : selectedItem?.type === 'time' ? (
              <AppTime
                placeholder={formatMessage({ id: DEFAULT_VALUE_PLACEHOLDER })}
              />
            ) : selectedItem?.type === 'date-time' ? (
              <AppDateTime
                placeholder={formatMessage({ id: DEFAULT_VALUE_PLACEHOLDER })}
              />
            ) : (
              <AppInput
                placeholder={formatMessage({ id: DEFAULT_VALUE_PLACEHOLDER })}
              />
            )}
          </Item>

          <Item
            name="description"
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'validation.fieldRequired' }),
              },
            ]}
          >
            <AppTextArea
              placeholder={formatMessage({
                id: 'schema.enterFieldDescription',
              })}
              autoSize={{ minRows: 3, maxRows: 10 }}
              asterisk
            />
          </Item>

          <Row justify="end">
            <Button type="primary" size="small" shape="round" htmlType="submit">
              {formatMessage({ id: 'common.save' })}
            </Button>
          </Row>
        </Form>
      </StyledChoicesContainer>
    </Modal>
  );
};

export default ManageDetails;
