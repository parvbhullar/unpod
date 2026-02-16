'use client';
import React, { Fragment, useEffect, useState } from 'react';
import { Button, Divider, Flex, Form, Typography } from 'antd';
import { generateHandle, getRandomColor } from '@unpod/helpers';
import {
  uploadPostDataApi,
  uploadPutDataApi,
  useAuthActionsContext,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { AppInput } from '@unpod/components/antd';
import { PUBLIC_EMAIL_DOMAIN } from '@unpod/constants/CommonConsts';
import { useSearchParams } from 'next/navigation';
import IdentityForm from './IdentityForm';
import { FooterBar } from '../../Onboarding/index.styled';
import {
  StyledDivider,
  StyledImportButton,
  StyledInputWithButton,
} from './index.styled';
import { setOrgHeader } from '@unpod/services';
import { useIntl } from 'react-intl';
import type { Organization, Pilot } from '@unpod/constants/types';

const { useForm } = Form;
const { Paragraph } = Typography;

const extractDomain = (url: string) => {
  return url
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .trim();
};

type DomainData = {
  company_name?: string;
  description?: string;
  ai_agent?: { name?: string; description?: string; persona?: string };
  visual?: { logo_url?: string; brand_colors?: string[] };
  [key: string]: unknown;
};

type IdentityStepProps = {
  agent?:
    | (Pilot & {
        privacy_type?: string;
        description?: string;
        handle?: string;
      })
    | null;
  updateAgentData: (
    formData: FormData,
    setLoading: (loading: boolean) => void,
  ) => void;
};

const IdentityStep = ({ agent, updateAgentData }: IdentityStepProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { updateAuthUser, setActiveOrg } = useAuthActionsContext();
  const { activeOrg, user } = useAuthContext();
  const [form] = useForm();
  const { formatMessage } = useIntl();

  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [domainUrl, setDomainUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [domainData, setDomainData] = useState<DomainData | null>(null);
  const [logoExternalUrl, setLogoExternalUrl] = useState<string | null>(null);

  const searchParams = useSearchParams();
  const agentHandle = searchParams?.get('handle');

  const [{ loading, apiData }, { setQueryParams }] = useGetDataApi(
    `core/website-info/`,
    {data: {}},
    {},
    false,
  ) as [
    { loading: boolean; apiData: { data?: DomainData } },
    { setQueryParams: (params: Record<string, unknown>) => void },
  ];

  useEffect(() => {
    if (!agentHandle && activeOrg?.domain_handle) {
      form.setFieldsValue({
        name: activeOrg.name,
        domain_handle: activeOrg.domain_handle,
      });
    }
  }, [activeOrg]);

  useEffect(() => {
    if (apiData.data && Object.keys(apiData.data).length > 0) {
      setDomainData(apiData.data);

      const data = {
        name: apiData.data.company_name,
        domain_handle: extractDomain(domainUrl),
        description: apiData.data.description,
      };

      form.setFieldsValue({ ...data });
    }
  }, [apiData.data]);

  useEffect(() => {
    if (agent) {
      if (agentHandle) {
        form.setFieldsValue({
          name: agent.name,
          description: agent.description,
          privacy_type: agent.privacy_type,
        });
      }
    }
  }, [agent]);

  const isValidDomain = () => {
    if (!domainUrl || typeof domainUrl !== 'string') return false;
    const domain = extractDomain(domainUrl)
      .toLowerCase()
      .replace(/\/.*$/, '')
      .trim();
    if (!domain) return false;
    // allow IPv4
    const ipRegex = /^(?:\d{1,3}\.){3}\d{1,3}$/;
    if (ipRegex.test(domain)) return true;

    // domain regex that accepts subdomains (e.g. app.example.com) and hyphens
    const domainRegex =
      /^(?=.{1,253}$)(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i;

    return domainRegex.test(domain);
  };

  const fetchDomainData = () => {
    if (!isValidDomain()) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'identityOnboarding.validDomain' }),
      );
    } else {
      const cleanDomain = extractDomain(domainUrl);
      const isPublic = PUBLIC_EMAIL_DOMAIN.includes(
        cleanDomain as (typeof PUBLIC_EMAIL_DOMAIN)[number],
      );

      if (isPublic) {
        infoViewActionsContext.showError(
          formatMessage({ id: 'identityOnboarding.publicDomain' }),
        );
        return;
      }

      setQueryParams({
        domain: cleanDomain,
        skipReset: true,
      });
    }
  };

  const saveAiAgent = (
    data: Record<string, any>,
    domainData: DomainData | null,
  ) => {
    const formData = new FormData();

    if (agentHandle) {
      formData.append('name', String(data.name || ''));
      formData.append('description', String(data.description || ''));
      formData.append('privacy_type', String(data.privacy_type || ''));
      formData.append(
        'handle',
        agent?.handle
          ? agent?.handle
          : generateHandle(String(data.name || ''), 5),
      );
      formData.append('type', 'Voice');

      if (logoFile) formData.append('logo', logoFile);
    } else {
      if (agent) {
        if (domainData) {
          const aiAgent = domainData.ai_agent;
          const aiName = aiAgent?.name || domainData.company_name || '';
          formData.append('name', aiName.substring(0, 98));
          formData.append('description', aiAgent?.description || '');
          formData.append('ai_persona', aiAgent?.persona || '');
        } else {
          formData.append('name', String(agent.name || ''));
          formData.append('description', String(agent.description || ''));
        }
      } else {
        if (domainData) {
          const aiAgent = domainData.ai_agent;
          const aiName = aiAgent?.name || domainData.company_name || '';
          formData.append('name', aiName.substring(0, 98));
          formData.append('description', aiAgent?.description || '');
          formData.append('ai_persona', aiAgent?.persona || '');
          formData.append('handle', generateHandle(String(aiName || ''), 5));
        } else {
          formData.append('name', String(data.name || ''));
          formData.append('description', String(data.description || ''));
          formData.append('handle', generateHandle(String(data.name || ''), 5));
        }
        formData.append('privacy_type', 'public');
        formData.append('type', 'Voice');
      }
    }

    updateAgentData(formData, setIsLoading);
  };

  const onFinish = (values: Record<string, any>) => {
    if (agentHandle) {
      saveAiAgent(values, null);
    } else {
      const orgFormData = new FormData();
      orgFormData.append('name', values.name);
      orgFormData.append('description', values.description);

      if (!activeOrg?.domain_handle) {
        // "#2874F0, #FF3E30"
        const colors = domainData?.visual?.brand_colors || [];
        const primaryColor = colors[0] || getRandomColor();
        orgFormData.append('domain_handle', values.domain_handle);
        orgFormData.append('privacy_type', 'public');
        orgFormData.append('account_type', 'business');
        orgFormData.append('region', 'IN');
        orgFormData.append('color', primaryColor);
      }

      if (logoFile) {
        orgFormData.append('logo', logoFile);
      } else if (logoExternalUrl) {
        orgFormData.append('logo_external_url', logoExternalUrl);
      }

      const orgRequestUrl = activeOrg?.domain_handle
        ? `organization/${activeOrg.domain_handle}/`
        : 'organization/';

      const orgApiMethod = activeOrg?.domain_handle
        ? uploadPutDataApi
        : uploadPostDataApi;

      orgApiMethod<Organization>(orgRequestUrl, infoViewActionsContext, orgFormData)
        .then((payload) => {
          if (!payload.data?.domain_handle) {
            return;
          }
          setOrgHeader(payload.data.domain_handle);

          if (activeOrg?.domain_handle) {
            const updatedHub = { ...activeOrg, ...payload.data };
            updateAuthUser({
              ...user,
              organization_list: (user?.organization_list || []).map((org) => {
                if (org.domain_handle === updatedHub.domain_handle) {
                  return updatedHub;
                }
                return org;
              }),
            });
            setActiveOrg(updatedHub);
          } else {
            updateAuthUser({
              ...user,
              organization: payload.data,
              active_organization: payload.data,
              organization_list: [
                ...(user?.organization_list || []),
                payload.data,
              ],
            });
            setActiveOrg(payload.data);
          }

          saveAiAgent(values, domainData);
        })
        .catch((error) => {
          const payload = error as { message?: string };
          infoViewActionsContext.showError(payload.message || '');
        });
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        privacy_type: 'public',
        ...agent,
      }}
      onFinish={onFinish}
    >
      {!agentHandle && (
        <Fragment>
          <Paragraph strong>Quick Import from Website</Paragraph>
          <Form.Item name="domain_url">
            <StyledInputWithButton>
              <AppInput
                placeholder={formatMessage({
                  id: 'identityOnboarding.domainUrl',
                })}
                asterisk
                onChange={(e) => setDomainUrl(e.target.value)}
              />
              <StyledImportButton
                size="small"
                type="primary"
                onClick={fetchDomainData}
                loading={loading}
              >
                {formatMessage({ id: 'identityOnboarding.import' })}
              </StyledImportButton>
            </StyledInputWithButton>
          </Form.Item>
          <StyledDivider>
            <Divider>
              {formatMessage({ id: 'identityOnboarding.orFillManually' })}
            </Divider>
          </StyledDivider>
        </Fragment>
      )}

      <IdentityForm
        form={form}
        domainData={domainData}
        logoExternalUrl={logoExternalUrl}
        setLogoExternalUrl={setLogoExternalUrl}
        setLogoFile={setLogoFile}
        agentData={agent}
      />

      <FooterBar>
        <Flex justify="flex-end" align="center">
          <Button
            type="primary"
            htmlType="submit"
            style={{ paddingLeft: 24, paddingRight: 24 }}
            loading={isLoading}
          >
            {formatMessage({ id: 'common.continue' })}
          </Button>
        </Flex>
      </FooterBar>
    </Form>
  );
};

export default IdentityStep;
