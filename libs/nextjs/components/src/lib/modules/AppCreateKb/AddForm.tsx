'use client';
import { useState } from 'react';

import { uploadDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { CONTACT_SPACE_FIELDS } from '@unpod/constants';
import { Button, Form, Space } from 'antd';
import { generateKbSchema } from '@unpod/helpers/AppKbHelper';
import {
  DrawerBody,
  DrawerForm,
  DrawerFormFooter,
} from '../../antd';
import GeneralForm from './GeneralForm';
import SchemaForm, { SchemaInput } from './SchemaForm';
import UploadDocumentForm from './UploadDocumentForm';
import { useIntl } from 'react-intl';

type CreateKbPayload = {
  name: string;
  description: string;
  content_type: string;
  privacy_type: string;
  invite_list?: string;
  schema?: string;
  [key: string]: any;
};

type AddFormProps = {
  onSaved?: (data: any) => void;
  content_type?: string;
  isSpace?: boolean;
  onClose?: () => void;
};

const AddForm = ({ onSaved, content_type, isSpace, onClose }: AddFormProps) => {
  const [form] = Form.useForm();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [loading, setLoading] = useState(false);
  const [contentType, setContentType] = useState(content_type);
  const [step, setStep] = useState(1);
  const [payload, setPayload] = useState<CreateKbPayload | null>(null);
  const [formInputs, setFormInputs] = useState<SchemaInput[]>([]);
  const [media, setMedia] = useState<File | null>(null);
  const [userList, setUserList] = useState<any[]>([]);
  const { formatMessage } = useIntl();

  const onBackClick = () => {
    if (step === 2) {
      setStep(step - 1);
    } else if (step === 3) {
      setStep(1);
    } else if (step === 4) {
      setStep(step - 2);
    }
  };

  const onNextClick = () => {
    if (step === 1) {
      setStep(3);
    } else {
      setStep(step + 1);
    }
  };

  const onCreateClick = () => {
    const validInputs = formInputs.filter((input) => input.title);
    const schema = generateKbSchema(validInputs);
    if (!payload) return;
    createKnowledgeBase({ ...payload, schema: JSON.stringify(schema) });
  };

  const createKnowledgeBase = (payload: CreateKbPayload) => {
    setLoading(true);
    const formData = new FormData();
    for (const key in payload) {
      formData.append(key, payload[key]);
    }
    formData.append('space_type', isSpace ? 'general' : 'knowledge_base');

    if (media) formData.append('files', media);

    uploadDataApi('spaces/', infoViewActionsContext, formData)
      .then((data: any) => {
        setLoading(false);
        localStorage.removeItem(`save-kb`);
        infoViewActionsContext.showMessage(data.message);
        if (onSaved) onSaved(data);
      })
      .catch((response: any) => {
        setLoading(false);
        infoViewActionsContext.showError(response.message);
      });
  };

  const onSubmitSuccess = (formData: CreateKbPayload) => {
    const payload: CreateKbPayload = {
      name: formData.name,
      description: formData.description || '',
      content_type: formData.content_type,
      privacy_type: formData.privacy_type,
    };
    const emptyInviteList = JSON.stringify([]);
    if (formData.privacy_type === 'shared') {
      payload.invite_list = userList
        ? JSON.stringify(userList)
        : emptyInviteList;
    } else {
      payload.invite_list = emptyInviteList;
    }

    if (contentType === 'table' || contentType === 'contact') {
      if (contentType === 'contact') {
        setFormInputs(CONTACT_SPACE_FIELDS);
      }
      setPayload(payload);
      onNextClick();
    } else {
      createKnowledgeBase(payload);
    }
  };

  return (
    <DrawerForm
      onFinish={onSubmitSuccess}
      form={form}
      initialValues={{
        content_type: contentType || 'contact',
        privacy_type: 'shared',
      }}
    >
      <DrawerBody>
        {step === 1 && (
          <GeneralForm
            isSpace={isSpace}
            setContentType={setContentType}
            form={form}
            userList={userList}
            setUserList={setUserList}
          />
        )}

        {step === 2 && (
          <SchemaForm
            formInputs={formInputs}
            setFormInputs={setFormInputs}
            contentType={contentType}
          />
        )}
        {step === 3 && (
          <UploadDocumentForm
            setMedia={setMedia}
            media={media}
            contentType={contentType}
            onEditSchema={() => setStep(2)}
          />
        )}
      </DrawerBody>

      <DrawerFormFooter>
        <>
          {step > 1 ? (
            <Space>
              {step > 1 && (
                <Button type="primary" onClick={onBackClick} ghost>
                  {formatMessage({ id: 'common.back' })}
                </Button>
              )}

              {step === 3 ? (
                <Button
                  type="primary"
                  onClick={onCreateClick}
                  loading={loading}
                >
                  {formatMessage({ id: 'common.save' })}
                </Button>
              ) : (
                <Button type="primary" onClick={onNextClick} loading={loading}>
                  {formatMessage({ id: 'common.next' })}
                </Button>
              )}
            </Space>
          ) : (
            <>
              <Button type="primary" onClick={onClose} ghost>
                {formatMessage({ id: 'common.cancel' })}
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                {contentType === 'table' || contentType === 'contact'
                  ? formatMessage({ id: 'common.next' })
                  : formatMessage({ id: 'common.save' })}
              </Button>
            </>
          )}
        </>
      </DrawerFormFooter>
    </DrawerForm>
  );
};

export default AddForm;
