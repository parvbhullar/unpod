import React, { Fragment, useEffect, useState } from 'react';
import type { FormInstance } from 'antd';
import { Form, Typography, Upload } from 'antd';
import { useSearchParams } from 'next/navigation';
import { PRIVACY_TYPES } from '@unpod/constants';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { AppInput, AppSelect, AppTextArea } from '@unpod/components/antd';
import AppImage from '@unpod/components/next/AppImage';
import {
  StyledInputWrapper,
  StyledItemWrapper,
  StylesImageWrapper,
} from './index.styled';
import {
  getDataApi,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useIntl } from 'react-intl';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';
import type { RcFile } from 'antd/es/upload/interface';
import type { Pilot } from '@unpod/constants/types';

const { Paragraph } = Typography;
const acceptTypes = ['image/png', 'image/jpeg', 'image/jpg'];
const { Item } = Form;

type DomainData = {
  visual?: { logo_url?: string };
  company_name?: string;
  description?: string;
  ai_agent?: { name?: string; description?: string; persona?: string };
  [key: string]: unknown;
};

type IdentityFormProps = {
  form: FormInstance;
  domainData: DomainData | null;
  setLogoFile: (file: File | null) => void;
  logoExternalUrl: string | null;
  setLogoExternalUrl: (url: string | null) => void;
  agentData?: Pilot | null;
};

const IdentityForm = ({
  form,
  domainData,
  setLogoFile,
  logoExternalUrl,
  setLogoExternalUrl,
  agentData,
}: IdentityFormProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { activeOrg, user } = useAuthContext();
  const searchParams = useSearchParams();
  const agentHandle = searchParams?.get('handle');
  const { formatMessage } = useIntl();

  const [logo, setLogo] = useState('');

  useEffect(() => {
    if (agentHandle) {
      if (agentData?.logo) {
        setLogo(agentData?.logo);
      }
    } else {
      if (activeOrg?.logo) {
        setLogo(activeOrg?.logo);
      }
    }
  }, [agentData?.logo, activeOrg?.logo]);

  useEffect(() => {
    if (domainData?.visual?.logo_url) {
      setLogoExternalUrl(domainData?.visual?.logo_url || null);
      setLogo('');
      setLogoFile(null);
    }
  }, [domainData?.visual?.logo_url]);

  const exclude = activeOrg?.org_id ? `?exclude_org=${activeOrg.org_id}` : '';

  const handleUploadChange = (file: RcFile) => {
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

    setLogoExternalUrl(null);
    setLogoFile(file);
    setLogo(URL.createObjectURL(file));
    return false;
  };

  return (
    <Fragment>
      <StyledItemWrapper>
        {agentHandle ? (
          <StyledInputWrapper>
            <Paragraph strong>
              {formatMessage({ id: 'onboarding.identitytitle' })}
            </Paragraph>
            <Item
              name="name"
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'validation.enterName',
                  }),
                },
                {
                  pattern: /^[a-zA-Z0-9\s'-]+$/,
                  message: formatMessage({
                    id: 'validation.validName',
                  }),
                },
              ]}
            >
              <AppInput
                placeholder={formatMessage({ id: 'form.name' })}
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
                placeholder="Privacy"
                options={(
                  getLocalizedOptions(
                    PRIVACY_TYPES as Array<{ key: string; label?: string }>,
                    formatMessage,
                  ) as Array<{ key?: string; label?: React.ReactNode }>
                ).map((option) => ({
                  label: option.label,
                  value: option.key || '',
                }))}
                asterisk
              />
            </Item>
          </StyledInputWrapper>
        ) : (
          <StyledInputWrapper>
            <Paragraph strong>
              {formatMessage({ id: 'onboarding.businessTitle' })}
            </Paragraph>
            <Item
              name="name"
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'validation.enterName',
                  }),
                },
                {
                  pattern: /^[a-zA-Z0-9\s'-]+$/,
                  message: formatMessage({
                    id: 'validation.validName',
                  }),
                },
              ]}
            >
              <AppInput
                placeholder={formatMessage({ id: 'form.name' })}
                asterisk
              />
            </Item>

            <Item
              name="domain_handle"
              rules={[
                {
                  required: false,
                  message: formatMessage({ id: 'validation.domain' }),
                },
                {
                  pattern: /^[a-zA-Z0-9\-._]+$/,
                  message: formatMessage({
                    id: 'validation.validName',
                  }),
                },
                {
                  validator: (_, value) => {
                    if (!value) return Promise.resolve();

                    // Check for URL patterns
                    const urlPattern = /^(https?:\/\/|www\.)/i;
                    const hasProtocol = urlPattern.test(value);
                    const hasPath = value.includes('/');

                    if (hasProtocol || hasPath) {
                      return Promise.reject(
                        new Error(
                          formatMessage({ id: 'validation.validDomain' }),
                        ),
                      );
                    }

                    return Promise.resolve();
                  },
                },
              ]}
            >
              <AppInput
                onBlur={(event: React.FocusEvent<HTMLInputElement>) => {
                  if (
                    event.target.value &&
                    event.target.value !== user?.domain
                  ) {
                    getDataApi(
                      `organization/check/?domain=${event.target.value}${exclude}`,
                      infoViewActionsContext,
                    )
                      .then((response) => {
                        const payload = response as {
                          data?: { exists?: boolean };
                          message?: string;
                        };
                        if (payload.data?.exists) {
                          form.setFields([
                            {
                              name: 'domain_handle',
                              errors: [payload.message || 'Already exists'],
                            },
                          ]);
                        }
                      })
                      .catch((error) => {
                        const payload = error as { message?: string };
                        infoViewActionsContext.showError(payload.message || '');
                      });
                  }
                }}
                placeholder={formatMessage({
                  id: 'validation.organizationDomain',
                })}
                asterisk
              />
            </Item>
          </StyledInputWrapper>
        )}

        <Upload
          accept=".png,.jpg,.jpeg"
          showUploadList={false}
          beforeUpload={handleUploadChange}
          maxCount={1}
        >
          <StylesImageWrapper>
            <AppImage
              src={logo || logoExternalUrl || '/images/logo_avatar.png'}
              alt="agent logo"
              height={90}
              width={90}
            />
          </StylesImageWrapper>
        </Upload>
      </StyledItemWrapper>

      <Item
        name="description"
        rules={[
          {
            required: true,
            message: formatMessage({ id: 'validation.enterDescription' }),
          },
        ]}
      >
        <AppTextArea
          placeholder={formatMessage({ id: 'form.description' })}
          asterisk
          rows={4}
          autosize={{ minRows: 4, maxRows: 6 }}
        />
      </Item>
    </Fragment>
  );
};

export default IdentityForm;
