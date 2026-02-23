import type {Dispatch, SetStateAction} from 'react';
import {memo, useEffect, useState} from 'react';
import type {UploadProps} from 'antd';
import {Button, Form, Upload} from 'antd';
import AppImage from '@unpod/components/next/AppImage';
import {AppInput, AppTextArea, DrawerBody, DrawerForm, DrawerFormFooter,} from '@unpod/components/antd';
import type {Spaces} from '@unpod/constants/types';
import {putDataApi, uploadPutDataApi, useInfoViewActionsContext,} from '@unpod/providers';
import {StyledEditContainer, StylesImageWrapper} from '../index.styled';
import {useIntl} from 'react-intl';

const {Item, useForm} = Form;

type EditSpaceProps = {
  onClose: () => void;
  currentSpace: Spaces | null;
  setCurrentSpace: Dispatch<SetStateAction<Spaces | null>>;
  $bodyHeight: number;
};

const EditSpace = ({
                     onClose,
                     currentSpace,
                     setCurrentSpace,
                     $bodyHeight,
                   }: EditSpaceProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [form] = useForm();
  const {formatMessage} = useIntl();

  const [spaceLogo, setSpaceLogo] = useState<string>(
    typeof currentSpace?.logo === 'string' ? currentSpace.logo : '',
  );

  useEffect(() => {
    form.setFieldsValue({
      name: currentSpace?.name,
      description: currentSpace?.description,
    });
  }, [currentSpace]);

  const onSubmitSuccess = (formData: Record<string, unknown>) => {
    if (!currentSpace?.slug) return;
    putDataApi(
      `spaces/${currentSpace?.slug}/`,
      infoViewActionsContext,
      formData,
    )
      .then((response) => {
        const res = response as { message?: string; data?: Spaces };
        if (res.message) infoViewActionsContext.showMessage(res.message);
        if (res.data) setCurrentSpace(res.data);
        onClose();
      })
      .catch((response) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const handleUploadChange: UploadProps['beforeUpload'] = (file) => {
    if (!currentSpace?.slug) return false;
    const formData = new FormData();
    formData.append('logo', file);
    uploadPutDataApi(
      `spaces/${currentSpace?.slug}/`,
      infoViewActionsContext,
      formData,
    )
      .then((response) => {
        const res = response as { message?: string; data?: Spaces };
        if (res.message) infoViewActionsContext.showMessage(res.message);
        if (typeof res.data?.logo === 'string') setSpaceLogo(res.data.logo);
        if (res.data) setCurrentSpace(res.data);
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
      });
    return false;
  };

  return (
    <DrawerForm form={form} onFinish={onSubmitSuccess}>
      <DrawerBody bodyHeight={$bodyHeight} isTabDrawer={true}>
        <StyledEditContainer>
          <Item
            name="name"
            rules={[
              {
                required: true,
                message: formatMessage({id: 'editSpace.validationName'}),
              },
            ]}
          >
            <AppInput
              placeholder={formatMessage({id: 'editSpace.namePlaceholder'})}
            />
          </Item>
          <Item
            name="description"
            rules={[
              {
                message: formatMessage({
                  id: 'editSpace.validationDescription',
                }),
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
        </StyledEditContainer>
      </DrawerBody>

      <DrawerFormFooter isTabDrawer={true}>
        <Button onClick={onClose}>
          {formatMessage({id: 'common.close'})}
        </Button>
        <Button type="primary" htmlType="submit">
          {formatMessage({id: 'common.save'})}
        </Button>
      </DrawerFormFooter>
    </DrawerForm>
  );
};

export default memo(EditSpace);
