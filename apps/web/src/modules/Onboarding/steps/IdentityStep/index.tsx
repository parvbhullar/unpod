'use client';
import React, { useEffect, useMemo, useState } from 'react';
import { Button, Divider, Flex, Form, Typography } from 'antd';
import { useIntl } from 'react-intl';
import { generateHandle } from '@unpod/helpers/StringHelper';
import {
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { FooterBar } from '@/modules/Onboarding/index.styled';
import { AppInput } from '@unpod/components/antd';
import { PUBLIC_EMAIL_DOMAIN } from '@unpod/constants/CommonConsts';
import { useSearchParams } from 'next/navigation';
import IdentityForm from './IdentityForm';
import KeyFeature from './KeyFeature';
import {
  StyledDivider,
  StyledImportButton,
  StyledInputWithButton,
} from './index.styled';
import { KEY_FEATURES } from '@unpod/constants';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';
import type { Pilot } from '@unpod/constants/types';

const { useForm } = Form;
const { Paragraph } = Typography;

const extractDomain = (url: string) => {
  return url
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .trim();
};

type IdentityStepProps = {
  agent: Pilot;
  updateAgentData: (
    formData: FormData,
    setLoading: React.Dispatch<React.SetStateAction<boolean>>,
    nextStep?: string,
  ) => void;
  setAgent: React.Dispatch<React.SetStateAction<Pilot>>;
  setDomainData: (data: Record<string, unknown>) => void;
};

type WebsiteInfoResponse = {
    key_features?: string[];
    company_name?: string;
    description?: string;
    [key: string]: unknown;
};

const IdentityStep: React.FC<IdentityStepProps> = ({
  agent,
  updateAgentData,
  setAgent,
  setDomainData,
}) => {
  void setAgent;
  const { formatMessage } = useIntl();
  const { activeOrg } = useAuthContext();
  const [form] = useForm();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [domainUrl, setDomainUrl] = useState('');
  const [keyFeatures, setKeyFeatures] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const searchParams = useSearchParams();
  const onboarded = searchParams?.get('onboarded') === 'true';

  const [{ loading, apiData }, { setQueryParams }] =
    useGetDataApi<WebsiteInfoResponse>(`core/website-info/`, {data:{}}, {}, false);

  useEffect(() => {
    const orgDomain = activeOrg?.domain || '';
    if (!domainUrl && !onboarded && orgDomain) {
      form.setFieldsValue({
        domain_url: orgDomain,
      });
      setDomainUrl(orgDomain);
    }
  }, [activeOrg, domainUrl, onboarded, form]);

  useEffect(() => {
    if (apiData.data && Object.keys(apiData.data).length > 0) {
      setKeyFeatures(apiData.data.key_features || []);
      setDomainData(apiData.data);

      const data = {
        name: apiData.data.company_name,
        description: apiData.data.description,
      };

      form.setFieldsValue({ ...data });
    }
  }, [apiData.data, form, setDomainData]);

  useEffect(() => {
    if (activeOrg?.domain_handle) {
      const cleanDomain = extractDomain(activeOrg.domain_handle);
      const isPublic = (PUBLIC_EMAIL_DOMAIN as readonly string[]).includes(
        cleanDomain,
      );

      if (!isPublic && !onboarded) {
        setQueryParams({
          domain: cleanDomain,
          skipReset: true,
        });
      }
    }
  }, [activeOrg?.domain_handle, onboarded, setQueryParams]);

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

  const getRecordByDomain = () => {
    if (!isValidDomain()) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'identityOnboarding.validDomain' }),
      );
      return;
    }

    const cleanDomain = extractDomain(domainUrl);
    const isPublic = (PUBLIC_EMAIL_DOMAIN as readonly string[]).includes(
      cleanDomain,
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
  };

  const onFinish = (values: {
    name: string;
    description: string;
    privacy_type: string;
    purpose: string;
    tags?: string[];
  }) => {
    /*if (privacyType === 'shared' && userList.length === 0) {
      infoViewActionsContext.showError('Please add at least one user.');
      return;
    }*/
    const formData = new FormData();

    // const filteredUsers =
    //   privacyType === 'shared'
    //     ? userList.filter(
    //         (user) => user && user.role_code !== ACCESS_ROLE.OWNER,
    //       )
    //     : [];

    // formData.append('user_list', JSON.stringify(filteredUsers));
    formData.append('name', values.name);
    formData.append('description', values.description);
    formData.append('privacy_type', values.privacy_type);
    formData.append(
      'handle',
      agent?.handle ? agent?.handle : generateHandle(values.name),
    );
    formData.append('type', 'Voice');
    formData.append('purpose', values.purpose);
    (values.tags || []).forEach((tag, item) =>
      formData.append(`tags[${item}]`, tag),
    );

    if (logoFile) formData.append('logo', logoFile);
    updateAgentData(formData, setIsLoading, '2');
  };

  const tags = useMemo(() => {
    const featureItems = Array.isArray(keyFeatures)
      ? keyFeatures.map((text, index) => ({ key: index, label: text }))
      : [];

    return featureItems.length > 0
      ? featureItems
      : getLocalizedOptions(KEY_FEATURES as any, formatMessage);
  }, [keyFeatures, formatMessage]);

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
      <Paragraph strong>
        {formatMessage({ id: 'identityOnboarding.quickImport' })}
      </Paragraph>
      <Form.Item name="domain_handle">
        <StyledInputWithButton>
          <AppInput
            placeholder={formatMessage({ id: 'identityOnboarding.domainUrl' })}
            asterisk
            onChange={(e) => setDomainUrl(e.target.value)}
          />

          <StyledImportButton
            size="small"
            type="primary"
            onClick={getRecordByDomain}
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

      <IdentityForm setLogoFile={setLogoFile} agentData={agent} />

      {tags.length > 0 && (
        <Form.Item
          name="tags"
          rules={[
            {
              required: true,
              message: formatMessage({
                id: 'validation.tags',
              }),
            },
          ]}
        >
          <KeyFeature
            apiFeatures={tags}
            label={formatMessage({ id: 'identityOnboarding.tags' })}
            initialSelected={[]}
            onChange={(val) => form.setFieldValue('tags', val)}
          />
        </Form.Item>
      )}

      <FooterBar>
        <Flex justify="flex-end" align="center">
          <Button
            type="primary"
            htmlType="submit"
            style={{ paddingLeft: 24, paddingRight: 24 }}
            loading={isLoading}
          >
            {formatMessage({ id: 'identityOnboarding.continue' })}
          </Button>
        </Flex>
      </FooterBar>
    </Form>
  );
};

export default IdentityStep;
