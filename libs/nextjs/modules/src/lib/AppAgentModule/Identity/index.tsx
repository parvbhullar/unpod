import {useEffect, useState} from 'react';
import type {FormInstance} from 'antd';
import {Button, Divider, Flex, Form} from 'antd';
import {SaveOutlined, TagsOutlined} from '@ant-design/icons';
import {useAuthContext, useGetDataApi, useInfoViewActionsContext, useInfoViewContext,} from '@unpod/providers';
import IdentityForm from './IdentityForm';
import {StickyFooter, StyledTabRoot,} from '../../AppIdentityAgentModule/index.styled';
import {StyledMainContainer} from './index.styled';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import CardWrapper from '@unpod/components/common/CardWrapper';
import {AppSelect} from '@unpod/components/antd';
import PurposeList from './PurposeList';
import {useIntl} from 'react-intl';
import {PURPOSE_CATEGORIES} from '@unpod/constants/CommonConsts';
import type {InviteMember, Pilot} from '@unpod/constants/types';

type IdentityProps = {
  agentData: Pilot;
  updateAgentData?: (data: FormData) => void;
  headerForm: FormInstance;
  hideNameField?: boolean;
};

type Tags = {
  name: string;
};


export type HeaderFormValues = {
  privacy_type: string;
  description?: string;
  purpose?: string;
  tags?: string[];
};

const Identity = ({
                    agentData,
                    updateAgentData,
                    headerForm,
                    hideNameField,
                  }: IdentityProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {loading} = useInfoViewContext();
  const [form] = Form.useForm();
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [userList, setUserList] = useState<InviteMember[]>([]);
  const privacyType = Form.useWatch('privacy_type', form);
  const {isAuthenticated} = useAuthContext();
  const {formatMessage} = useIntl();


  const [{apiData}, {reCallAPI}] = useGetDataApi<Tags[]>(
    'core/tags/',
    {data: []},
    {},
    false,
  );

  useEffect(() => {
    if (isAuthenticated) reCallAPI();
  }, [isAuthenticated]);

  useEffect(() => {
    if (privacyType === 'public') {
      setUserList([]);
      form.setFieldsValue({sharedFields: []});
    }
  }, [privacyType]);

  useEffect(() => {
    if (agentData?.users) {
      setUserList(agentData.users);
    }
  }, [agentData?.users]);

  const onFormSave = (value: HeaderFormValues) => {
    if (privacyType === 'shared' && userList.length === 0) {
      infoViewActionsContext.showError(
        formatMessage({id: 'validation.addAtLeastOneUser'}),
      );
      return;
    }

    const formData = new FormData();
    const filteredUsers =
      privacyType === 'shared'
        ? userList.filter(
          (user: InviteMember) =>
            user && user.role_code !== ACCESS_ROLE.OWNER,
        )
        : [];

    formData.append('user_list', JSON.stringify(filteredUsers));
    formData.append('name', headerForm.getFieldValue('name'));
    formData.append('privacy_type', value?.privacy_type);
    formData.append('description', value.description || '');
    formData.append('purpose', value.purpose || '');
    formData.append('type', 'Voice');

    if (agentData?.space_slug) {
      formData.append('space_slug', agentData?.space_slug as string);
    }

    (value.tags || []).forEach((tag: string) => formData.append(`tags`, tag));

    if (logoFile) {
      formData.append('logo', logoFile);
    }
    updateAgentData?.(formData);
  };

  return (
    <Form
      layout="vertical"
      form={form}
      initialValues={{
        name: agentData?.name,
        privacy_type: agentData?.privacy_type || 'public',
        description: agentData?.description,
        purpose: agentData?.purpose || 'Business',
        tags: agentData?.tags,
      }}
      onFinish={onFormSave}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          <IdentityForm
            setLogoFile={(file: File) => setLogoFile(file)}
            agentData={agentData}
            privacyType={privacyType}
            setUserList={(users: InviteMember[]) => setUserList(users)}
            userList={userList}
            hideNameField={hideNameField}
          />

          <CardWrapper
            icon={<TagsOutlined/>}
            title={formatMessage({id: 'aiStudio.identityClassification'})}
          >
            <Form.Item
              help={formatMessage({
                id: 'aiStudio.identityClassificationHelp',
              })}
              name="tags"
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'validation.classificationMessage',
                  }),
                },
              ]}
            >
              <AppSelect
                placeholder={formatMessage({
                  id: 'aiStudio.identityclassificationplaceholder',
                })}
                mode="tags"
                options={apiData?.data?.map((item: Tags) => ({
                  key: item.name,
                  label: item.name,
                  value: item.name,
                }))}
              />
            </Form.Item>
            <Form.Item
              name="purpose"
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'validation.purpose',
                  }),
                },
              ]}
            >
              <PurposeList
                items={PURPOSE_CATEGORIES}
                label={formatMessage({id: 'identityOnboarding.purpose'})}
              />
            </Form.Item>
          </CardWrapper>
        </StyledMainContainer>
      </StyledTabRoot>

      <StickyFooter>
        <Divider/>
        <Flex justify="end">
          <Button
            htmlType="submit"
            type="primary"
            icon={<SaveOutlined/>}
            loading={loading}
          >
            {formatMessage({id: 'common.save'})}
          </Button>
        </Flex>
      </StickyFooter>
    </Form>
  );
};

export default Identity;
