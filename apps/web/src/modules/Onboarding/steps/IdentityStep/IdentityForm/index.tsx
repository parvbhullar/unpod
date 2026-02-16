import React, { Fragment, useEffect, useState } from 'react';
import { Form, Typography, Upload, type UploadProps } from 'antd';
import { useIntl } from 'react-intl';
import { PRIVACY_TYPES, PURPOSE_CATEGORIES } from '@unpod/constants';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { AppInput, AppSelect, AppTextArea } from '@unpod/components/antd';
import AppImage from '@unpod/components/next/AppImage';
import PurposeList from '../PurposeList';
import {
  StyledInputWrapper,
  StyledItemWrapper,
  StylesImageWrapper,
} from './index.styled';
import { useInfoViewActionsContext } from '@unpod/providers';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';
import type { Pilot } from '@unpod/constants/types';

const { Paragraph } = Typography;

const acceptTypes = ['image/png', 'image/jpeg', 'image/jpg'];

const { Item } = Form;

type IdentityFormProps = {
  setLogoFile: React.Dispatch<React.SetStateAction<File | null>>;
  agentData?: Pilot | null;
};

const IdentityForm: React.FC<IdentityFormProps> = ({
  setLogoFile,
  agentData,
}) => {
  const { formatMessage } = useIntl();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [logo, setLogo] = useState('');

  useEffect(() => {
    const nextLogo =
      typeof (agentData as { logo?: unknown })?.logo === 'string'
        ? (agentData as { logo?: string }).logo
        : '';
    if (nextLogo) {
      setLogo(nextLogo);
    }
  }, [agentData]);

  const handleUploadChange: NonNullable<UploadProps['beforeUpload']> = (
    file,
  ) => {
    const extension = getFileExtension(file.name).toLowerCase();

    const isAllowedExtension = acceptTypes
      ?.map((t) => t.toLowerCase())
      .includes(extension);
    const isAllowedMime = file.type && acceptTypes?.includes(file.type);

    if (!isAllowedExtension && !isAllowedMime) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'validation.fileTypeNotAllowed' }),
      );
      return false;
    }

    setLogoFile(file);
    setLogo(URL.createObjectURL(file));
    return false;
  };

  return (
    <Fragment>
      <StyledItemWrapper>
        <StyledInputWrapper>
          <Paragraph strong>
            {formatMessage({ id: 'identityOnboarding.identityName' })}
          </Paragraph>
          <Item
            name="name"
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'validation.enterName' }),
              },
              {
                pattern: /^[a-zA-Z0-9\s'-]+$/,
                // message: formatMessage({ id: 'validation.enterName' }),
                message: formatMessage({ id: 'validation.validName' }),
              },
            ]}
          >
            <AppInput
              placeholder={formatMessage({
                id: 'identityOnboarding.identityNamePlaceholder',
              })}
              asterisk
            />
          </Item>

          <Item
            name="privacy_type"
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'validation.privacyType',
                }),
              },
            ]}
          >
            <AppSelect
              placeholder={formatMessage({ id: 'identityOnboarding.privacy' })}
              options={getLocalizedOptions(PRIVACY_TYPES as any, formatMessage)}
              asterisk
            />
          </Item>
        </StyledInputWrapper>

        <Upload
          accept=".png,.jpg,.jpeg"
          showUploadList={false}
          beforeUpload={handleUploadChange}
          maxCount={1}
        >
          <StylesImageWrapper>
            <AppImage
              src={logo ? logo : '/images/logo_avatar.png'}
              alt="agent logo"
              height={90}
              width={90}
            />
          </StylesImageWrapper>
        </Upload>
      </StyledItemWrapper>

      <Item
        name="purpose"
        rules={[
          {
            required: true,
            message: formatMessage({ id: 'validation.purpose' }),
          },
        ]}
      >
        <PurposeList
          items={PURPOSE_CATEGORIES}
          label={formatMessage({ id: 'identityOnboarding.purpose' })}
        />
      </Item>

      <Item
        name="description"
        rules={[
          {
            required: true,
            message: formatMessage({
              id: 'validation.enterDescription',
            }),
          },
        ]}
      >
        <AppTextArea
          placeholder={formatMessage({ id: 'identityOnboarding.description' })}
          asterisk
          rows={4}
          autosize={{ minRows: 4, maxRows: 6 }}
        />
      </Item>
    </Fragment>
  );
};

export default IdentityForm;
