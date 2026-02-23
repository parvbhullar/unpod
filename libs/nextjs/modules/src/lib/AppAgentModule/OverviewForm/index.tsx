import {useEffect, useState} from 'react';
import {Button, Flex, Form, Image, Radio, Select, Upload} from 'antd';
import {FileImageOutlined, InfoCircleOutlined, SaveOutlined, TagsOutlined, UploadOutlined,} from '@ant-design/icons';
import {useAuthContext, useGetDataApi, useInfoViewActionsContext, useInfoViewContext,} from '@unpod/providers';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import {AppSelect, AppTextArea} from '@unpod/components/antd';
import CardWrapper from '@unpod/components/common/CardWrapper';
import AppSharedUserList from '@unpod/components/common/AppSharedUserList';
import {LogoContainer, StyledUploadButton, StyleFormItemPrivacy, StylesImageWrapper,} from './index.styled';
import {MdBusinessCenter} from 'react-icons/md';
import {FaHeart, FaUser} from 'react-icons/fa';
import {DiRequirejs} from 'react-icons/di';
import {StickyFooter, StyledMainContainer, StyledTabRoot,} from '../index.styled';
import PurposeList from './PurposeLIst';

const purposeCategory = {
  sectionLabel: 'Purpose',
  items: [
    {
      key: 'Business',
      label: 'Business Functions',
      desc: 'Sales Assistant, Support Agent, Lead Qualifier',
      icon: <MdBusinessCenter size={24}/>,
      color: '#9d5c06ff',
    },
    {
      key: 'Personal',
      label: 'Personal Functions',
      desc: 'Study Buddy, Fitness Coach, Personal Assistant',
      icon: <FaUser size={24}/>,
      color: '#979492ff',
    },
    {
      key: 'Service',
      label: 'Service Functions',
      desc: 'Booking Agent, Healthcare Assistant, Concierge',
      icon: <FaHeart size={24}/>,
      color: '#e70000ff',
    },
  ],
};

const MobileAwareTextArea = (props: any) => {
  const [placeholder, setPlaceholder] = useState(
    "Describe your agent's capabilities, expertise, and purpose...",
  );

  const handleFocus = () => {
    if (typeof window !== 'undefined' && window.innerWidth <= 768) {
      setPlaceholder('');
    }
  };

  const handleBlur = () => {
    if (typeof window !== 'undefined' && window.innerWidth <= 768) {
      setPlaceholder(
        "Describe your agent's capabilities, expertise, and purpose...",
      );
    }
  };

  return (
    <AppTextArea
      {...props}
      placeholder={placeholder}
      onFocus={handleFocus}
      onBlur={handleBlur}
    />
  );
};

type OverviewFormProps = {
  agentData?: any;
  updateAgentData?: (data: FormData) => void;
  headerForm: any;
};

const OverviewForm = ({
                        agentData,
                        updateAgentData,
                        headerForm,
                      }: OverviewFormProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {loading} = useInfoViewContext();
  const {isAuthenticated} = useAuthContext();
  const [form] = Form.useForm();
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logo, setLogo] = useState(agentData?.logo || '');
  const [userList, setUserList] = useState<any[]>([]);
  const privacyType = Form.useWatch('privacy_type', form);

  const [{apiData}, {reCallAPI}] = useGetDataApi(
    'core/tags/',
    {data: []},
    {},
    false,
  ) as [
    { apiData: { data?: Array<{ name: string }> } },
    { reCallAPI: () => void },
  ];

  useEffect(() => {
    if (isAuthenticated) reCallAPI();
  }, [isAuthenticated]);

  const onLogoUpload = (file?: File) => {
    if (!file) {
      return false;
    }
    const extension = file.name.split('.').pop()?.toLowerCase() || '';
    if (!['png', 'jpg', 'jpeg'].includes(extension)) {
      infoViewActionsContext.showError('File type not allowed. Use PNG/JPG.');
      return false;
    }
    setLogoFile(file);
    setLogo(window.URL.createObjectURL(file));
    return false;
  };

  useEffect(() => {
    if (agentData) {
      form.setFieldsValue({
        name: agentData?.name,
        tags:
          agentData?.tags?.map((tag: any) =>
            typeof tag === 'object' ? tag.name : tag,
          ) || [],
        privacy_type: agentData?.privacy_type || 'public',
        description: agentData?.description,
      });
    }
  }, [agentData]);

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

  const onFormSave = (value: any) => {
    if (privacyType === 'shared' && userList.length === 0) {
      infoViewActionsContext.showError('Please add at least one user.');
      return;
    }

    const formData = new FormData();
    const filteredUsers =
      privacyType === 'shared'
        ? userList.filter(
          (user: any) => user && user.role_code !== ACCESS_ROLE.OWNER,
        )
        : [];

    formData.append('name', headerForm.getFieldValue('name'));
    formData.append('privacy_type', value?.privacy_type);
    formData.append('type', headerForm.getFieldValue('type'));
    formData.append('description', value.description || '');
    formData.append('user_list', JSON.stringify(filteredUsers));
    formData.append('purpose', value.purpose || '');
    if (headerForm.getFieldValue('region'))
      formData.append('region', headerForm.getFieldValue('region'));

    if (agentData?.space_slug) {
      formData.append('space_slug', agentData?.space_slug);
    }

    (value.tags || []).forEach((tag: string, item: number) =>
      formData.append(`tags[${item}]`, tag),
    );

    if (logoFile) {
      formData.append('logo', logoFile);
    }

    updateAgentData?.(formData);
  };

  /*  const handleOnValidateSave = async () => {
    Promise.all([headerForm.validateFields(), form.validateFields()])
      .then((formPayloads) => {
        const overviewFormValues = formPayloads[1];
        onFormSave(overviewFormValues);
      })
      .catch(() => {
        infoViewActionsContext.showError('Please fill required fields');
      });
  };*/

  return (
    <Form
      layout="vertical"
      form={form}
      onFinish={onFormSave}
      initialValues={{
        name: agentData?.name,
        tags:
          agentData?.tags?.map((tag: any) =>
            typeof tag === 'object' ? tag.name : tag,
          ) || [],
        privacy_type: agentData?.privacy_type || 'public',
        description: agentData?.description,
        purpose: agentData?.purpose,
      }}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          <CardWrapper icon={<InfoCircleOutlined/>} title="Description">
            <Form.Item
              name="description"
              help="Provide a detailed description of what your agent can do"
              rules={[
                {
                  required: true,
                  message: 'Please provide a description for your agent',
                },
              ]}
            >
              <MobileAwareTextArea rows={6}/>
            </Form.Item>

            <StyleFormItemPrivacy
              name="privacy_type"
              rules={[
                {
                  required: true,
                  message: 'Please select a privacy type',
                },
              ]}
            >
              <Radio.Group size="large">
                <Radio.Button value="public">Public</Radio.Button>
                <Radio.Button value="shared">Shared</Radio.Button>
              </Radio.Group>
            </StyleFormItemPrivacy>

            {privacyType === 'shared' && (
              <Form.Item name="sharedFields">
                <AppSharedUserList
                  users={userList}
                  onChangeUsers={setUserList}
                />
              </Form.Item>
            )}
          </CardWrapper>

          <CardWrapper icon={<DiRequirejs size={18}/>} title="Purpose">
            <Form.Item
              name="purpose"
              rules={[
                {required: true, message: 'Please select at least one tone'},
              ]}
            >
              <PurposeList
                items={purposeCategory.items}
                label={purposeCategory.sectionLabel}
                title={false}
              />
            </Form.Item>
          </CardWrapper>

          <CardWrapper icon={<TagsOutlined/>} title="Classification">
            <Form.Item
              help="Keywords to help users discover your agent"
              name="tags"
              rules={[
                {
                  required: true,
                  message: 'Please add at least one tag',
                },
              ]}
            >
              <AppSelect placeholder="Select Tags" mode="tags">
                {apiData?.data?.map((item: { name: string }) => (
                  <Select.Option key={item.name} value={item.name}>
                    {item.name}
                  </Select.Option>
                ))}
              </AppSelect>
            </Form.Item>
          </CardWrapper>

          <CardWrapper icon={<FileImageOutlined/>} title="Logo">
            <Form.Item help="Upload a logo image for your agent (PNG, JPG up to 5MB)">
              <LogoContainer align="center">
                <StylesImageWrapper>
                  <Image
                    src={logo || agentData?.logo || '/images/logo_avatar.png'}
                    alt="agent logo"
                    height={90}
                    width={90}
                    preview={!!(logo || agentData?.logo)}
                  />
                </StylesImageWrapper>

                <Upload
                  accept=".png,.jpg,.jpeg"
                  showUploadList={false}
                  beforeUpload={onLogoUpload}
                  maxCount={1}
                >
                  <StyledUploadButton icon={<UploadOutlined/>} type="primary">
                    {logo ? 'Change Logo' : 'Upload Logo'}
                  </StyledUploadButton>
                </Upload>
              </LogoContainer>
            </Form.Item>
          </CardWrapper>
        </StyledMainContainer>
      </StyledTabRoot>

      <StickyFooter>
        <Flex justify="end">
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined/>}
            loading={loading}
          >
            Save
          </Button>
        </Flex>
      </StickyFooter>
    </Form>
  );
};

export default OverviewForm;
