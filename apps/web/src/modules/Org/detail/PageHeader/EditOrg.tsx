import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { AppGridContainer, AppInput } from '@unpod/components/antd';
import { Button, Col, Form, Row, Upload, type UploadProps } from 'antd';
import {
  putDataApi,
  uploadPutDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import styled from 'styled-components';
import { StyledEditRoot } from './index.styled';
import type { Organization } from '@unpod/constants/types';

export const UserUploadImg = styled.img`
  width: 80px;
  height: 80px;
  object-fit: cover;
`;

type EditHubProps = {
  onClose: () => void;
};

const EditHub: React.FC<EditHubProps> = ({ onClose }) => {
  const { formatMessage } = useIntl();
  const { activeOrg: currentHub } = useAuthContext();
  const { setActiveOrg } = useAuthActionsContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [orgLogo, setHubLogo] = useState(currentHub?.logo || '');
  const [form] = Form.useForm();

  useEffect(() => {
    if (currentHub) {
      form.setFieldsValue({
        name: currentHub?.name,
      });
    }
  }, [currentHub]);

  const onSubmitSuccess = (formData: Record<string, unknown>) => {
    if (currentHub) {
      putDataApi<unknown>(
        `organization/${currentHub.domain_handle}/`,
        infoViewActionsContext,
        formData,
      )
        .then((response) => {
          const res = response as {
            message?: string;
            data?: Organization;
          };
          infoViewActionsContext.showMessage(res.message || 'Updated');
          setActiveOrg({ ...currentHub, ...(res.data || {}) });
          onClose();
        })
        .catch((response) => {
          const err = response as { message?: string };
          infoViewActionsContext.showError(err.message || 'Error');
        });
    }
  };

  const handleUploadChange: NonNullable<UploadProps['beforeUpload']> = (
    info,
  ) => {
    const formData = new FormData();
    formData.append('logo', info);
    uploadPutDataApi<any>(
      `organization/${currentHub?.domain_handle}/`,
      infoViewActionsContext,
      formData,
    )
      .then((data) => {
        const res = data;
        infoViewActionsContext.showMessage(res.message || 'Updated');
        setHubLogo(res.data?.logo || '');
      })
      .catch((error) => {
        const err = error as { message?: string };
        infoViewActionsContext.showError(err.message || 'Error');
      });
    return false;
  };

  return (
    <StyledEditRoot>
      <AppGridContainer>
        <Col sm={24} md={16}>
          <Form form={form} onFinish={onSubmitSuccess}>
            <AppGridContainer>
              <Col sm={24}>
                <Form.Item
                  name="name"
                  rules={[
                    {
                      required: true,
                      message: formatMessage({ id: 'hub.enterName' }),
                    },
                  ]}
                >
                  <AppInput placeholder={formatMessage({ id: 'hub.name' })} />
                </Form.Item>
              </Col>
            </AppGridContainer>

            <Row>
              <Button type="primary" htmlType="submit">
                {formatMessage({ id: 'hub.updateHub' })}
              </Button>
            </Row>
          </Form>
        </Col>

        {currentHub ? (
          <Col sm={24} md={8}>
            <Upload
              accept=".png, .jpg,.jpeg"
              showUploadList={false}
              beforeUpload={handleUploadChange}
              maxCount={1}
            >
              <UserUploadImg
                src={orgLogo ? orgLogo : '/images/no_download.png'}
                alt="logo"
              />
            </Upload>
          </Col>
        ) : null}
      </AppGridContainer>
    </StyledEditRoot>
  );
};

export default EditHub;
