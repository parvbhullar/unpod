import { useCallback, useEffect, useState } from 'react';
import type { FormInstance } from 'antd';
import { Form, Radio, Select, Space } from 'antd';
import {
  COLLECTION_TYPE_DATA,
  contentTypeData,
  PERMISSION_TYPES,
} from '@unpod/constants';
import { AppInput, AppSelect, AppTextArea } from '../../../antd';
import { getDraftData, saveDraftData } from '@unpod/helpers/DraftHelper';
import _debounce from 'lodash/debounce';
import AppSharedUserList from '../../../common/AppSharedUserList';
import { useIntl } from 'react-intl';
import { getStatusOptionsFromConfig } from '@unpod/helpers/LocalizationFormatHelper';

type DraftData = {
  title?: string;
  description?: string;
  content_type?: string;
  privacy?: string;
  users?: any[];
};

type GeneralFormProps = {
  isSpace?: boolean;
  setContentType: (value: string) => void;
  form: FormInstance;
  userList: any[];
  setUserList: (users: any[]) => void;
};

const GeneralForm = ({
  isSpace,
  setContentType,
  form,
  userList,
  setUserList,
}: GeneralFormProps) => {
  const [dataFetched, setDataFetched] = useState(false);
  const debounceFn = useCallback(_debounce(saveDraftData, 2000), []);
  const title = Form.useWatch('name', form);
  const contentType = Form.useWatch('content_type', form);
  const description = Form.useWatch('description', form);
  const privacyType = Form.useWatch('privacy_type', form);
  const { formatMessage } = useIntl();

  useEffect(() => {
    if (dataFetched) {
      debounceFn(`save-kb`, {
        title: title,
        description: description,
        content_type: contentType,
        privacy: privacyType,
        users: userList,
      });
    }
    setContentType(contentType);
  }, [title, description, contentType, privacyType, userList, dataFetched]);

  useEffect(() => {
    if (!dataFetched) {
      const draftData = getDraftData(`save-kb`) as DraftData | null;
      setUserList(draftData?.users || []);
      form.setFieldsValue({
        name: draftData?.title || '',
        description: draftData?.description || '',
        content_type: draftData?.content_type || 'contact',
        privacy_type: draftData?.privacy || 'shared',
      });
      setTimeout(() => {
        setDataFetched(true);
      }, 1000);
    }
  }, [dataFetched]);

  return (
    <>
      <Form.Item
        name="name"
        rules={[
          {
            required: true,
            message: isSpace
              ? formatMessage({ id: 'validation.enterSpaceName' })
              : formatMessage({ id: 'validation.enterKnowledgeBaseName' }),
          },
        ]}
      >
        <AppInput
          placeholder={
            isSpace
              ? formatMessage({ id: 'space.spaceName' })
              : formatMessage({ id: 'knowledgeBase.pageTitle' })
          }
        />
      </Form.Item>

      <Form.Item
        name="content_type"
        rules={[
          {
            required: true,
            message: formatMessage({ id: 'validation.selectContentType' }),
          },
        ]}
      >
        <AppSelect placeholder={formatMessage({ id: 'form.contentType' })}>
          {(isSpace
            ? (getStatusOptionsFromConfig(
                COLLECTION_TYPE_DATA as any,
                formatMessage,
              ) as any)
            : (getStatusOptionsFromConfig(
                contentTypeData as any,
                formatMessage,
              ) as any)
          )?.map((role: any) => (
            <Select.Option key={role.id} value={role.id}>
              <Space>
                {role?.icon}
                {role.name}
              </Space>
            </Select.Option>
          ))}
        </AppSelect>
      </Form.Item>

      {/* <Form.Item
        name="privacy_type"
        rules={[
          {
            required: true,
            message: 'Please select a privacy type',
          },
        ]}
      >
        <Dropdown
          menu={{
            items:  getLocalizedOptions(PERMISSION_TYPES, formatMessage),
            onClick: onChangePrivacy,
            selectedKeys: currentPrivacy?.key,
          }}
          trigger={['click']}
          disabled={open}
        >

          <Link>
            <Space>
              {currentPrivacy?.icon}
              <span>{formatMessage({id:currentPrivacy?.label})}</span>
            </Space>
          </Link>
        </Dropdown>
        <PostPermissionPopover
          open={open}
          setOpen={setOpen}
          userList={userList}
          setUserList={setUserList}
          placement="topRight"
        />
      </Form.Item> */}
      <Form.Item name="description">
        <AppTextArea
          placeholder={formatMessage({ id: 'form.description' })}
          autoSize={{
            minRows: 5,
            maxRows: 50,
          }}
        />
      </Form.Item>
      <Form.Item
        name="privacy_type"
        rules={[
          {
            required: true,
            message: formatMessage({ id: 'validation.selectPrivacy' }),
          },
        ]}
      >
        <Radio.Group size="large">
          {PERMISSION_TYPES.map((item: any) => (
            <Radio.Button key={item.key} value={item.key}>
              <Space>
                {item?.icon}
                <span>{formatMessage({ id: item?.label })}</span>
              </Space>
            </Radio.Button>
          ))}
        </Radio.Group>
      </Form.Item>
      {privacyType === 'shared' && (
        <AppSharedUserList users={userList} onChangeUsers={setUserList} />
      )}
    </>
  );
};

export default GeneralForm;
