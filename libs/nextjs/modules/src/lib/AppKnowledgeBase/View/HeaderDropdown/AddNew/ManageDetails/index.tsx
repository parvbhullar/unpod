import React from 'react';
import { Button, Form, Modal, Row } from 'antd';
import { StyledChoicesContainer } from './index.styled';
import { AppInput, AppSelect, AppTextArea } from '@unpod/components/antd';
import { getMachineName } from '@unpod/helpers/StringHelper';
import { useIntl } from 'react-intl';

const { Item } = Form;

const ManageDetails = ({
  selectedItem,
  onFinish,
  initialValues,
  ...restProps
}) => {
  const { formatMessage } = useIntl();

  return (
    <Modal
      title={formatMessage({ id: 'schema.manageDetails' })}
      footer={null}
      destroyOnHidden
      centered
      {...restProps}
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
              placeholder={formatMessage({
                id: 'schema.enterFieldTitle',
              })}
              asterisk
            />
          </Item>

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
              placeholder={formatMessage({
                id: 'schema.enterFieldName',
              })}
              asterisk
            />
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
                placeholder={formatMessage({ id: 'schema.enterChoices' })}
                mode="tags"
                asterisk
              />
            </Item>
          )}

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
