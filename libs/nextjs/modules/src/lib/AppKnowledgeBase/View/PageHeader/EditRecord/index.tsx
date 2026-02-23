'use client';
import {useEffect, useState} from 'react';
import {putDataApi, useInfoViewActionsContext} from '@unpod/providers';
import {Button, Col, Form} from 'antd';
import {AppGridContainer, AppInput, AppTextArea, DrawerBody, DrawerFooter, DrawerForm,} from '@unpod/components/antd';
import {useIntl} from 'react-intl';

type EditRecordProps = {
  onClose: () => void;
  currentKb: any;
  setCurrentKb: (kb: any) => void;
};

const EditRecord = ({onClose, currentKb, setCurrentKb}: EditRecordProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const {formatMessage} = useIntl();

  useEffect(() => {
    if (currentKb) {
      form.setFieldsValue({
        name: currentKb.name,
        description: currentKb.description,
      });
    }
  }, [currentKb, form]);

  const handleSubmit = (values: Record<string, any>) => {
    setLoading(true);
    putDataApi(`spaces/${currentKb.slug}/`, infoViewActionsContext, values)
      .then((response: any) => {
        setLoading(false);
        infoViewActionsContext.showMessage(response.message);
        setCurrentKb(response.data);
        onClose();
      })
      .catch((error: any) => {
        setLoading(false);
        infoViewActionsContext.showError(error.message);
      });
  };

  return (
    <DrawerForm form={form} onFinish={handleSubmit}>
      <DrawerBody>
        <AppGridContainer>
          <Col span={24}>
            <Form.Item
              name="name"
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'validation.enterKnowledgeBase',
                  }),
                },
              ]}
            >
              <AppInput
                placeholder={formatMessage({id: 'knowledgeBase.pageTitle'})}
              />
            </Form.Item>
          </Col>

          <Col span={24}>
            <Form.Item name="description">
              <AppTextArea
                placeholder={formatMessage({id: 'form.description'})}
                maxLength={250}
                rows={4}
              />
            </Form.Item>
          </Col>
        </AppGridContainer>
      </DrawerBody>

      <DrawerFooter>
        <Button onClick={onClose} style={{marginRight: 8}}>
          {formatMessage({id: 'common.cancel'})}
        </Button>
        <Button type="primary" htmlType="submit" loading={loading}>
          {formatMessage({id: 'common.update'})}
        </Button>
      </DrawerFooter>
    </DrawerForm>
  );
};

export default EditRecord;
