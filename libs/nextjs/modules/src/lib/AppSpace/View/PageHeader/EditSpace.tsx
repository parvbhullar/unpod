import { memo, useEffect, useState } from 'react';
import { Button, Col, Form, Row, Upload } from 'antd';
import AppImage from '@unpod/components/next/AppImage';
import {
  AppGridContainer,
  AppInput,
  AppTextArea,
} from '@unpod/components/antd';
import {
  putDataApi,
  uploadPutDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { StyledRoot, StylesImageWrapper } from './index.styled';
import { useIntl } from 'react-intl';

const { Item, useForm } = Form;

const EditSpace = ({
  onClose,
  currentSpace,
  setCurrentSpace,
}: {
  onClose: () => void;
  currentSpace: any;
  setCurrentSpace: (space: any) => void;
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [form] = useForm();
  const { formatMessage } = useIntl();

  const [spaceLogo, setSpaceLogo] = useState(currentSpace?.logo || '');

  useEffect(() => {
    form.setFieldsValue({
      name: currentSpace?.name,
      description: currentSpace?.description,
    });
  }, [currentSpace]);

  const onSubmitSuccess = (formData: any) => {
    putDataApi(
      `spaces/${currentSpace?.slug}/`,
      infoViewActionsContext,
      formData,
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        setCurrentSpace(response.data);
        onClose();
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const handleUploadChange = (info: any) => {
    const formData = new FormData();
    formData.append('logo', info);
    uploadPutDataApi(
      `spaces/${currentSpace?.slug}/`,
      infoViewActionsContext,
      formData,
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        setSpaceLogo(response.data.logo);
        setCurrentSpace(response.data);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
    return false;
  };

  return (
    <StyledRoot>
      <Form form={form} onFinish={onSubmitSuccess}>
        <AppGridContainer>
          <Col sm={24}>
            <Item
              name="name"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.spaceName' }),
                },
              ]}
            >
              <AppInput
                placeholder={formatMessage({ id: 'editSpace.namePlaceholder' })}
              />
            </Item>
          </Col>

          <Col sm={24}>
            <Item
              name="description"
              rules={[
                {
                  message: formatMessage({ id: 'validation.spaceDesc' }),
                },
              ]}
            >
              <AppTextArea
                placeholder={formatMessage({
                  id: 'editSpace.descriptionPlaceholder',
                })}
                maxLength={250}
                rows={4}
              />
            </Item>
          </Col>

          <Col sm={24}>
            <Upload
              accept=".png, .jpg,.jpeg"
              showUploadList={false}
              beforeUpload={handleUploadChange}
              maxCount={1}
            >
              <StylesImageWrapper>
                <AppImage
                  src={spaceLogo ? spaceLogo : '/images/no_download.png'}
                  alt="logo"
                  height={150}
                  width={150}
                  objectFit="cover"
                />
              </StylesImageWrapper>
            </Upload>
          </Col>
        </AppGridContainer>

        <Row>
          <Button type="primary" htmlType="submit">
            {formatMessage({ id: 'space.update' })}
          </Button>
        </Row>
      </Form>
    </StyledRoot>
  );
};

export default memo(EditSpace);
