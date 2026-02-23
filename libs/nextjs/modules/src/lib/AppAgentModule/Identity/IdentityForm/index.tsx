import {Fragment, useEffect, useState} from 'react';
import {Form, Space, Typography, Upload} from 'antd';
import {StyledInputWrapper, StyledItemWrapper, StylesImageWrapper,} from './index.styled';
import {PRIVACY_TYPES} from '@unpod/constants';
import {getFileExtension} from '@unpod/helpers/FileHelper';
import {AppInput, AppSelect, AppTextArea} from '@unpod/components/antd';
import {MdOutlinePrivacyTip} from 'react-icons/md';
import AppSharedUserList from '@unpod/components/common/AppSharedUserList';
import CardWrapper from '@unpod/components/common/CardWrapper';
import AppImage from '@unpod/components/next/AppImage';
import {IoInformationCircleOutline} from 'react-icons/io5';
import {useIntl} from 'react-intl';
import {useInfoViewActionsContext} from '@unpod/providers';
import type {InviteMember, Pilot} from '@unpod/constants/types';

const {Paragraph} = Typography;

const acceptTypes = ['image/png', 'image/jpeg', 'image/jpg'];

const {Item} = Form;

type IdentityFormProps = {
  setLogoFile: (file: File) => void;
  agentData: Pilot;
  privacyType?: string;
  setUserList?: (users: InviteMember[]) => void;
  userList?: InviteMember[];
  hideNameField?: boolean;
};

const IdentityForm = ({
                        setLogoFile,
                        agentData,
                        privacyType,
                        setUserList,
                        userList,
                        hideNameField = false,
                      }: IdentityFormProps) => {
  const [logo, setLogo] = useState('');
  const {formatMessage} = useIntl();
  const infoViewActionsContext = useInfoViewActionsContext();

  useEffect(() => {
    if (agentData) {
      setLogo(agentData?.logo || '');
    }
  }, [agentData]);

  const handleUploadChange = (file: File) => {
    const extension = getFileExtension(file.name).toLowerCase();

    const isAllowedExtension = acceptTypes
      ?.map((t) => t.toLowerCase())
      .includes(extension);
    const isAllowedMime = file.type && acceptTypes?.includes(file.type);

    if (!isAllowedExtension && !isAllowedMime) {
      infoViewActionsContext.showError(
        formatMessage({id: 'upload.errorInvalidFileType'}),
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
          {!hideNameField && (
            <>
              <Paragraph strong>
                {formatMessage({id: 'identityOnboarding.identityName'})}
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
                      id: 'validation.validName"',
                    }),
                  },
                ]}
              >
                <AppInput
                  placeholder={formatMessage({
                    id: 'identityOnboarding.identityName',
                  })}
                  asterisk
                />
              </Item>
            </>
          )}

          <CardWrapper
            title={formatMessage({id: 'identityOnboarding.description'})}
            icon={<IoInformationCircleOutline size={17}/>}
          >
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
                placeholder={formatMessage({
                  id: 'identityOnboarding.description',
                })}
                asterisk
                rows={4}
                autosize={{minRows: 4, maxRows: 6}}
              />
            </Item>
          </CardWrapper>
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

      <CardWrapper
        title={formatMessage({id: 'identityOnboarding.privacy'})}
        icon={<MdOutlinePrivacyTip/>}
      >
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
            placeholder={formatMessage({
              id: 'identityOnboarding.privacy',
            })}
            options={PRIVACY_TYPES.map((item) => ({
              ...item,
              label: (
                <Space>
                  {item.icon}
                  {formatMessage({id: item.label})}
                </Space>
              ),
            }))}
            asterisk
          />
        </Item>

        {privacyType === 'shared' && (
          <Form.Item name="sharedFields">
            <AppSharedUserList users={userList} onChangeUsers={setUserList}/>
          </Form.Item>
        )}
      </CardWrapper>
    </Fragment>
  );
};

export default IdentityForm;
