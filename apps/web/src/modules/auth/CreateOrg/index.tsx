'use client';
import type { ChangeEvent } from 'react';
import { useEffect, useState } from 'react';
import type { UploadFile } from 'antd';
import { Button, Col, Form, Space, Typography, Upload } from 'antd';
import {
  StyledContainer,
  StyledTitle,
  StylesImageWrapper,
} from './index.styled';
import {
  getDataApi,
  uploadPostDataApi,
  uploadPutDataApi,
  useAuthActionsContext,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useRouter } from 'next/navigation';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import { AppGridContainer, AppInput, AppSelect } from '@unpod/components/antd';
import { getRandomColor } from '@unpod/helpers/StringHelper';
import { PRIVACY_TYPES } from '@unpod/constants';

import { getFileExtension } from '@unpod/helpers/FileHelper';
import AppImage from '@unpod/components/next/AppImage';
import { setOrgHeader } from '@unpod/services';
import ItemCell from '@/modules/auth/CreateOrg/ItemCell';
import { regionOptions } from '@unpod/constants/CountryData';
import { useIntl } from 'react-intl';
import type { LocalizableOption } from '@unpod/helpers/LocalizationFormatHelper';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';
import type { Organization } from '@unpod/constants/types';
import type { RcFile } from 'antd/es/upload/interface';

const acceptTypes = ['image/png', 'image/jpeg', 'image/jpg'];

type CreateOrgProps = {
  org?: Organization | null;
};

type OrgFormValues = {
  name: string;
  privacy_type: string;
  account_type: string;
  region: string;
  domain_handle?: string;
};

type AccountTypeItem = {
  slug?: string;
  title?: string;
  description?: string;
  [key: string]: unknown;
};

const CreateOrg = ({ org }: CreateOrgProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { updateAuthUser, setActiveOrg } = useAuthActionsContext();
  const { user } = useAuthContext();
  const { formatMessage } = useIntl();
  const [form] = Form.useForm<OrgFormValues>();
  const [logo, setLogo] = useState(org?.logo ? org.logo : '');
  const [logoFile, setLogoFile] = useState<UploadFile | File | null>(null);
  const [selectedItem, setSelectedItem] = useState<string[] | string>(
    org?.account_type ?? '',
  );

  const router = useRouter();
  const [{ apiData }] = useGetDataApi<AccountTypeItem[]>(
    'roles/tags/roles/',
    { data: [] },
    {},
  );

  useEffect(() => {
    if (user && !org) {
      form.setFieldsValue({
        domain_handle: user.domain,
      });
    }
  }, [user, org]);

  useEffect(() => {
    if (org) {
      form.setFieldsValue({
        ...org,
        account_type: org.account_type?.[0] ?? '',
      });
      setLogo(org?.logo ? `${org.logo}?tr=w-80,h-80` : '');
    }
  }, [org]);

  const onSubmitSuccess = (values: OrgFormValues) => {
    const formData = new FormData();
    formData.append('name', values.name);
    formData.append('privacy_type', values.privacy_type);
    formData.append('account_type', values.account_type || '');
    formData.append('region', values.region);
    if (org) {
      if (logoFile) {
        const fileObj =
          (logoFile as UploadFile).originFileObj || (logoFile as File);
        if (fileObj) formData.append('logo', fileObj as Blob);
      }

      uploadPutDataApi(
        `organization/${org.domain_handle}/`,
        infoViewActionsContext,
        formData,
      )
        .then((response) => {
          const typedResponse = response as {
            message?: string;
            data?: Organization;
          };
          infoViewActionsContext.showMessage(typedResponse.message || 'Saved');

          const updatedHub = { ...org, ...(typedResponse.data || {}) };

          setLogo(`${updatedHub.logo}?tr=w-80,h-80`);
          updateAuthUser({
            ...user,
            organization_list: (user?.organization_list || []).map((orgItem) =>
              orgItem.domain_handle === updatedHub.domain_handle
                ? updatedHub
                : orgItem,
            ),
          });
          setActiveOrg(updatedHub);
        })
        .catch((response: { message?: string }) => {
          infoViewActionsContext.showError(
            response.message || 'Failed to save',
          );
        });
    } else {
      if (logoFile) {
        const fileObj =
          (logoFile as UploadFile).originFileObj || (logoFile as File);
        if (fileObj) formData.append('logo', fileObj as Blob);
      }
      formData.append('color', getRandomColor());
      if (values.domain_handle) {
        formData.append('domain_handle', values.domain_handle);
      }
      uploadPostDataApi(
        'organization/',
        infoViewActionsContext,
        formData,
      )
        .then((response) => {
          const typedResponse = response as {
            message?: string;
            data?: Organization;
          };
          infoViewActionsContext.showMessage(typedResponse.message || 'Saved');
          setOrgHeader(typedResponse.data?.domain_handle || '');
          updateAuthUser({
            ...user,
            organization: typedResponse.data,
            active_organization: typedResponse.data,
            organization_list: [
              ...(user?.organization_list || []),
              ...(typedResponse.data ? [typedResponse.data] : []),
            ],
          });
          if (typedResponse.data) {
            setActiveOrg(typedResponse.data);
          }
          if (process.env.productId === 'unpod.ai') {
            router.push('/ai-identity');
          } else {
            router.push(`/org`);
          }
          // router.push('/seeking');
        })
        .catch((response: { message?: string }) => {
          infoViewActionsContext.showError(
            response.message || 'Failed to create',
          );
        });
    }
  };
  const onSelectAccount = (item: AccountTypeItem) => {
    if (!item.slug) return;
    setSelectedItem(item.slug);
    form.setFieldsValue({
      account_type: item.slug,
    });
  };

  const handleUploadChange = (file: RcFile | UploadFile) => {
    const extension = getFileExtension(file.name);
    if (
      acceptTypes &&
      !acceptTypes.includes(extension) &&
      (!file.type || !acceptTypes.includes(file.type))
    ) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'validation.fileTypeNotAllowed' }),
      );
    } else {
      const fileObj = (file as UploadFile).originFileObj || (file as File);
      setLogoFile(fileObj || null);
      if (fileObj) {
        setLogo(window.URL.createObjectURL(fileObj as Blob));
      }
    }
    return false;
  };

  return (
    <AppPageLayout layout="full">
      <Form
        form={form}
        initialValues={{
          domain_handle: user?.is_private_domain ? user?.domain_handle : '',
          privacy_type: org ? org.privacy_type : 'public',
          ...org,
        }}
        onFinish={onSubmitSuccess}
        style={{ width: '100%' }}
      >
        <StyledContainer>
          {org ? null : (
            <StyledTitle>
              {formatMessage({ id: 'org.createTitle' })}
            </StyledTitle>
          )}

          <AppGridContainer gutter={28}>
            <Col xs={24} md={20}>
              <Form.Item
                name="name"
                rules={[
                  {
                    required: true,
                    message: formatMessage({ id: 'validation.orgName' }),
                  },
                ]}
              >
                <AppInput
                  placeholder={formatMessage({ id: 'org.placeholderName' })}
                  asterisk
                />
              </Form.Item>

              <Form.Item
                name="domain_handle"
                rules={[
                  {
                    required: false,
                    message: formatMessage({ id: 'validation.orgDomain' }),
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
                  readOnly={user?.is_private_domain}
                  disabled={!!org}
                  onBlur={(e: ChangeEvent<HTMLInputElement>) => {
                    if (
                      e.target.value === user?.domain ||
                      e.target.value === ''
                    )
                      return;
                    getDataApi(
                      `organization/check/?domain=${e.target.value}`,
                      infoViewActionsContext,
                    )
                      .then((response) => {
                        const typedResponse = response as {
                          data?: { exists?: boolean };
                          message?: string;
                        };
                        if (typedResponse.data?.exists) {
                          form.setFields([
                            {
                              name: 'domain_handle',
                              errors: [
                                typedResponse.message ||
                                  'Domain already exists',
                              ],
                            },
                          ]);
                        }
                      })
                      .catch((error: { message?: string }) => {
                        infoViewActionsContext.showError(
                          error.message || 'Failed to validate domain',
                        );
                      });
                  }}
                  placeholder={formatMessage({ id: 'org.placeholderDomain' })}
                  asterisk
                />
              </Form.Item>

              <Form.Item
                name="privacy_type"
                rules={[
                  {
                    required: true,
                    message: formatMessage({ id: 'validation.orgPrivacy' }),
                  },
                ]}
              >
                <AppSelect
                  placeholder={formatMessage({ id: 'org.privacyPlaceholder' })}
                  options={getLocalizedOptions(
                    PRIVACY_TYPES as unknown as LocalizableOption[],
                    formatMessage,
                  )}
                />
              </Form.Item>

              <Form.Item
                name="region"
                initialValue="IN"
                rules={[
                  {
                    required: true,
                    message: formatMessage({ id: 'validation.orgRegion' }),
                  },
                ]}
              >
                <AppSelect
                  disabled={!!org}
                  placeholder={formatMessage({ id: 'common.selectRegion' })}
                  options={regionOptions}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={4}>
              <Upload
                accept=".png, .jpg,.jpeg"
                showUploadList={false}
                beforeUpload={handleUploadChange}
                maxCount={1}
              >
                <StylesImageWrapper>
                  <AppImage
                    src={logo ? logo : '/images/logo_avatar.png'}
                    alt="logo"
                    height={80}
                    width={80}
                    objectFit="cover"
                  />
                </StylesImageWrapper>
              </Upload>
            </Col>

            <Col xs={24}>
              <Typography.Paragraph>
                {formatMessage({ id: 'org.accountSuits' })}
              </Typography.Paragraph>

              <Form.Item
                name="account_type"
                rules={[
                  {
                    required: true,
                    message: formatMessage({ id: 'validation.orgAccountType' }),
                  },
                ]}
              >
                <Space orientation="vertical">
                  {apiData?.data?.map((item) => {
                    return (
                      <ItemCell
                        key={item.slug}
                        onSelectAccount={onSelectAccount}
                        selectedItem={selectedItem}
                        item={item}
                      />
                    );
                  })}
                </Space>
              </Form.Item>
            </Col>
          </AppGridContainer>
          <div style={{ textAlign: 'right' }}>
            <Button type="primary" htmlType="submit" style={{ minWidth: 120 }}>
              {org
                ? formatMessage({ id: 'common.save' })
                : formatMessage({ id: 'common.next' })}
            </Button>
          </div>
        </StyledContainer>
      </Form>
    </AppPageLayout>
  );
};

export default CreateOrg;
