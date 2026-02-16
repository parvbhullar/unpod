import { useState } from 'react';
import { Button, Form } from 'antd';
import { MdAdd, MdDelete, MdOutlineAddIcCall } from 'react-icons/md';
import { AppInput, AppTextArea } from '@unpod/components/antd';
import { MOBILE_REGX } from '@unpod/constants';
import type { Spaces } from '@unpod/constants/types';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';
import {
  StyledBottomBar,
  StyledItemRow,
  StyledLabel,
  StyledRoot,
} from './index.styled';

const { ErrorList, Item, List, useForm } = Form;

type VoiceCallProps = {
  currentSpace: Spaces | null;
  onCallSent: (data: unknown) => void;
};

const VoiceCall = ({ currentSpace, onCallSent }: VoiceCallProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [loading, setLoading] = useState(false);
  const [form] = useForm();

  const onFinish = (values: Record<string, unknown>) => {
    if (!currentSpace?.token) return;
    setLoading(true);
    const payload = {
      ...values,
      pilot: `space-agent-${currentSpace.token}`,
      execution_type: 'outbound_call',
    };
    console.log('Received values:', payload);

    postDataApi(
      `tasks/space-task/${currentSpace?.token}/`,
      infoViewActionsContext,
      payload,
    )
      .then((response) => {
        setLoading(false);
        const res = response as { message?: string; data?: unknown };
        if (res.message) infoViewActionsContext.showMessage(res.message);
        form.resetFields();
        onCallSent(res.data);
      })
      .catch((error) => {
        infoViewActionsContext.showMessage(error.message);
        setLoading(false);
      });
  };

  return (
    <StyledRoot>
      <Form
        onFinish={onFinish}
        form={form}
        initialValues={{
          users: [{ name: '', phone_number: '' }],
        }}
      >
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
          />
        </Item>

        <StyledLabel>People</StyledLabel>
        <List
          name="users"
          rules={[
            {
              validator: async (_, users) => {
                if (!users || users.length < 1) {
                  return Promise.reject(
                    new Error('At least 1 people required'),
                  );
                }
              },
            },
          ]}
        >
          {(fields, { add, remove }, { errors }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <StyledItemRow key={key}>
                  <Item
                    {...restField}
                    name={[name, 'name']}
                    rules={[
                      {
                        required: true,
                        message: 'This field is required',
                      },
                    ]}
                  >
                    <AppInput placeholder="Name" asterisk />
                  </Item>

                  <Item
                    {...restField}
                    name={[name, 'phone_number']}
                    rules={[
                      {
                        required: true,
                        message: 'This field is required',
                      },
                      () => ({
                        validator(_, value) {
                          if (!value) {
                            return Promise.resolve();
                          }
                          if (!MOBILE_REGX.test(value)) {
                            return Promise.reject(
                              'Please enter a valid phone No.',
                            );
                          }
                          return Promise.resolve();
                        },
                      }),
                    ]}
                  >
                    <AppInput placeholder="Phone No." asterisk />
                  </Item>

                  <Item>
                    <Button
                      type="primary"
                      onClick={() => remove(name)}
                      icon={<MdDelete fontSize={18} />}
                      danger
                      ghost
                    />
                  </Item>
                </StyledItemRow>
              ))}

              <Item>
                <ErrorList errors={errors} />
                <Button
                  type="dashed"
                  onClick={() => add()}
                  block
                  icon={<MdAdd />}
                >
                  Add New
                </Button>
              </Item>
            </>
          )}
        </List>

        <StyledBottomBar>
          <Button
            type="primary"
            shape="round"
            htmlType="submit"
            icon={<MdOutlineAddIcCall fontSize={18} />}
            loading={loading}
          >
            Call
          </Button>
        </StyledBottomBar>
      </Form>
    </StyledRoot>
  );
};

export default VoiceCall;
