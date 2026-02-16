import { useEffect, useState } from 'react';
import { Button, Form, Radio, Typography } from 'antd';
import {
  AppDrawer,
  AppInput,
  AppPassword,
  AppSelect,
  DrawerBody,
  DrawerForm,
  DrawerFormFooter,
} from '@unpod/components/antd';
import { patchDataApi, useInfoViewActionsContext } from '@unpod/providers';

const { Item, useForm } = Form;
const { Group: RadioGroup, Button: RadioButton } = Radio;
const { Paragraph } = Typography;

type EditTrunkProps = {
  item: any;
  open: boolean;
  onClose: () => void;
  onUpdated: (item: any) => void;
};

const EditTrunk = ({ item, open, onClose, onUpdated }: EditTrunkProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [form] = useForm();

  const [loading, setLoading] = useState(false);
  const [direction, setDirection] = useState('');

  useEffect(() => {
    if (item) {
      form.setFieldsValue({
        name: item?.name,
        direction: item?.direction || '',
        address: item?.address,
        media_encryption: item?.media_encryption || 'enabled',
        username: item?.username,
        password: item?.password,
      });

      setDirection(item?.direction || '');
    }
  }, [item, form]);

  const onSubmit = (values: any) => {
    setLoading(true);
    const payload = {
      ...values,
      bridge_slug: item.bridge_slug,
      direction: values.direction || direction,
    };

    patchDataApi(
      `telephony/trunks/${item.id}/`,
      infoViewActionsContext,
      payload,
      false,
    )
      .then((res: any) => {
        setLoading(false);
        infoViewActionsContext.showMessage(res?.message);
        onUpdated(res?.data);
      })
      .catch((err: any) => {
        setLoading(false);
        infoViewActionsContext.showError(err?.message);
        onClose();
      });
  };

  return (
    <AppDrawer
      title="Update Trunk"
      open={open}
      onClose={onClose}
      showLoader
      loading={loading}
    >
      <DrawerForm layout="vertical" form={form} onFinish={onSubmit}>
        <DrawerBody>
          <Item
            name="name"
            rules={[{ required: true, message: 'Please enter trunk name' }]}
          >
            <AppInput placeholder="Trunk name" />
          </Item>

          {direction && (
            <Paragraph>
              <Item label="Direction" name="direction">
                <RadioGroup
                  onChange={(event: any) => setDirection(event.target.value)}
                >
                  <RadioButton value="inbound">Inbound</RadioButton>
                  <RadioButton value="outbound">Outbound</RadioButton>
                  <RadioButton value="both">Both</RadioButton>
                </RadioGroup>
              </Item>
            </Paragraph>
          )}

          <Item
            name="address"
            rules={[
              {
                required: direction === 'outbound',
              },
              {
                validator: (_: any, value: any) => {
                  if (!value) return Promise.resolve();

                  const ipRegex =
                    /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/;
                  const hostRegex =
                    /^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$/;

                  if (ipRegex.test(value) || hostRegex.test(value)) {
                    return Promise.resolve();
                  }
                  return Promise.reject(
                    new Error(
                      'Please enter a valid IP address or hostname (e.g. 192.168.0.1 or sip.example.com)',
                    ),
                  );
                },
              },
            ]}
          >
            <AppInput placeholder="IP address or hostname" />
          </Item>

          <Item name="media_encryption">
            <AppSelect
              placeholder="Media encryption (SRTP)"
              options={[
                { label: 'Media encryption disabled', value: 'disabled' },
                { label: 'Media encryption enabled', value: 'enabled' },
              ]}
            />
          </Item>

          <Item name="username">
            <AppInput placeholder="Username" />
          </Item>

          <Item name="password">
            <AppPassword placeholder="Password" />
          </Item>
        </DrawerBody>
        <DrawerFormFooter>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="primary" htmlType="submit">
            Update
          </Button>
        </DrawerFormFooter>
      </DrawerForm>
    </AppDrawer>
  );
};

export default EditTrunk;
