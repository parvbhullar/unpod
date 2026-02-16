'use client';
import React, { useEffect, useState } from 'react';
import { Button, Form, Modal, ModalProps, Row, Select } from 'antd';
import { getMachineName } from '@unpod/helpers/StringHelper';
import {
  AppDate,
  AppDateTime,
  AppInput,
  AppSelect,
  AppTextArea,
  AppTime,
} from '../../../antd';
import { REQUIRED_CONTACT_FIELDS } from '@unpod/constants';
import { StyledRoot } from './index.styled';

const { Item } = Form;
const { Option } = Select;

const DEFAULT_VALUE_PLACEHOLDER = 'Enter Default Value';

type SelectedItemType = {
  name?: string;
  type?: string;
  choices?: string[];
  isEnum?: boolean;};

type AppRowOptionsProps = Omit<ModalProps, 'onFinish'> & {
  selectedItem?: SelectedItemType;
  onFinish?: (values: Record<string, unknown>) => void;
  initialValues?: Record<string, unknown>;
  contentType?: string;
  isDecRequired?: boolean;};

const AppRowOptions: React.FC<AppRowOptionsProps> = ({
  selectedItem,
  onFinish,
  initialValues,
  contentType,
  isDecRequired,
  ...restProps
}) => {
  const [choices, setChoices] = useState<string[]>([]);
  const isRequiredContactField =
    !!selectedItem?.name &&
    (REQUIRED_CONTACT_FIELDS as readonly string[]).includes(selectedItem.name);

  useEffect(() => {
    if (selectedItem?.choices) {
      setChoices(selectedItem.choices);
    }
  }, [selectedItem]);

  const handleChoicesChange = (value: string[]) => {
    setChoices(value);
  };
  return (
    <Modal
      title="Manage Options"
      footer={null}
      destroyOnHidden
      centered
      {...restProps}
    >
      <StyledRoot>
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
                message: 'This field is required',
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
            <AppInput placeholder={`Enter Field Title`} asterisk />
          </Item>

          {!(contentType === 'contact' && isRequiredContactField) && (
            <Item
              name="name"
              rules={[
                {
                  required: true,
                  message: 'This field is required',
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
              <AppInput placeholder={`Enter Field Name`} asterisk />
            </Item>
          )}

          {(selectedItem?.type === 'select' ||
            selectedItem?.type === 'multi-select' ||
            selectedItem?.type === 'checkboxes' ||
            selectedItem?.isEnum) && (
            <Item
              name="choices"
              rules={[
                {
                  required: true,
                  message: 'This field is required',
                },
              ]}
            >
              <AppSelect
                placeholder={`Enter Choices`}
                onChange={(value) =>
                  handleChoicesChange((value as string[]) || [])
                }
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
                message: 'This field is required',
              },
            ]}
          >
            {selectedItem?.type === 'select' ||
            selectedItem?.type === 'multi-select' ||
            selectedItem?.type === 'checkboxes' ? (
              <AppSelect
                placeholder={DEFAULT_VALUE_PLACEHOLDER}
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
              <AppDate placeholder={DEFAULT_VALUE_PLACEHOLDER} />
            ) : selectedItem?.type === 'time' ? (
              <AppTime placeholder={DEFAULT_VALUE_PLACEHOLDER} />
            ) : selectedItem?.type === 'date-time' ? (
              <AppDateTime placeholder={DEFAULT_VALUE_PLACEHOLDER} />
            ) : (
              <AppInput placeholder={DEFAULT_VALUE_PLACEHOLDER} />
            )}
          </Item>

          <Item
            name="description"
            rules={[
              {
                required: isDecRequired,
                message: 'This field is required',
              },
            ]}
          >
            <AppTextArea
              placeholder={`Enter Field Description`}
              autoSize={{ minRows: 3, maxRows: 10 }}
              asterisk={isDecRequired}
            />
          </Item>

          <Row justify="end">
            <Button type="primary" size="small" shape="round" htmlType="submit">
              Save
            </Button>
          </Row>
        </Form>
      </StyledRoot>
    </Modal>
  );
};

export default AppRowOptions;
