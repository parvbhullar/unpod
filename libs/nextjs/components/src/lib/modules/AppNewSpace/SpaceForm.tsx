import React, {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';
import PropTypes from 'prop-types';
import { Button, Dropdown, Form, Row, Select, Space, Typography } from 'antd';
import _debounce from 'lodash/debounce';
import { MdAdd, MdArrowUpward } from 'react-icons/md';
import { uploadDataApi, useInfoViewActionsContext } from '@unpod/providers';
import {
  allowedFileTypes,
  CONTACT_SPACE_FIELDS,
  PERMISSION_TYPES,
  SPACE_CONTENT_TYPES,
} from '@unpod/constants';
import { useOrgActionContext } from '@unpod/providers';
import { getDraftData, saveDraftData } from '@unpod/helpers/DraftHelper';
import { randomId } from '@unpod/helpers/GlobalHelper';
import { getMachineName } from '@unpod/helpers/StringHelper';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { generateKbSchema } from '@unpod/helpers/AppKbHelper';
import PostPermissionPopover from '../../common/PermissionPopover/PostPermissionPopover';
import {
  AppMiniWindowBody,
  AppMiniWindowFooter,
} from '../../common/AppMiniWindow';
import ManageDetails from '../AppKbSchemaManager/ManageDetails';
import InputRow from '../AppKbSchemaManager/InputRow';
import AppInputSelector from '../../antd/AppInputSelector';
import {
  StyledButton,
  StyledDragger,
  StyledFormItem,
  StyledInput,
  StyledList,
  StyledMediaWrapper,
  StyledSelect,
  StyledStepContainer,
  StyledStickyButton,
  StyledTextArea,
} from './index.styled';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';
import { useIntl } from 'react-intl';

const { Option } = Select;
const { Link, Paragraph, Text } = Typography;

const SpaceForm = ({ content_type, onSaved }) => {
  const [form] = Form.useForm();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { currentSpace } = useOrgActionContext();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [privacyType, setPrivacyType] = useState('shared');
  const [currentPrivacy, setCurrentPrivacy] = useState(null);
  const [userList, setUserList] = useState([]);
  const [title, setTitle] = useState(null);
  const [description, setDescription] = useState(null);
  const [contentType, setContentType] = useState(null);
  const [step, setStep] = useState(1);
  const [isSkipped, setSkipped] = useState(false);
  const [payload, setPayload] = useState(null);
  const { formatMessage } = useIntl();

  const [inputModalOpen, setInputModalOpen] = useState(false);
  const [formInputs, setFormInputs] = useState([]);
  const [openDetail, setOpenDetail] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [media, setMedia] = useState(null);

  const [dataFetched, setDataFetched] = useState(false);
  const debounceFn = useCallback(_debounce(saveDraftData, 2000), []);

  useEffect(() => {
    if (dataFetched) {
      debounceFn(`save-space`, {
        title: title,
        description: description,
        content_type: contentType,
        privacy: privacyType,
        users: userList,
      });
    }
  }, [title, description, contentType, privacyType, userList, dataFetched]);

  useEffect(() => {
    if (!dataFetched) {
      const draftData = getDraftData(`save-space`);

      if (draftData) {
        setTitle(draftData.title);
        setDescription(draftData.description);
        setContentType(content_type || draftData.content_type);
        setPrivacyType(draftData.privacy);
        setUserList(draftData.users);

        form.setFieldsValue({
          name: draftData.title,
          description: draftData.description,
          content_type: content_type || draftData.content_type,
        });
      } else {
        setContentType(content_type || 'general');
        form.setFieldsValue({
          content_type: content_type || 'general',
        });
      }

      setTimeout(() => {
        setDataFetched(true);
      }, 1000);
    }
  }, [dataFetched, content_type]);

  useEffect(() => {
    setCurrentPrivacy(
      PERMISSION_TYPES.find((item) => item.key === privacyType),
    );
  }, [privacyType]);

  const acceptFileTypes = useMemo(() => {
    return allowedFileTypes[contentType || 'table'];
  }, [contentType]);

  const addNewSpace = (payload) => {
    setLoading(true);
    const formData = new FormData();
    for (const key in payload) {
      formData.append(key, payload[key]);
    }

    if (media) formData.append('files', media);

    formData.append('space_type', 'general');
    formData.append('privacy_type', privacyType);

    if (privacyType === 'shared') {
      formData.append('invite_list', JSON.stringify(userList));
    } else {
      formData.append('invite_list', JSON.stringify([]));
    }

    uploadDataApi('spaces/', infoViewActionsContext, formData)
      .then((data) => {
        setLoading(false);
        localStorage.removeItem(`save-space`);
        infoViewActionsContext.showMessage(data.message);
        if (onSaved) onSaved(data);
      })
      .catch((response) => {
        setLoading(false);
        infoViewActionsContext.showError(response.message);
      });
  };

  const onShareChange = (option) => {
    if (option.key === 'shared') {
      setOpen(true);
    }

    setPrivacyType(option.key);
  };

  const onTitleChange = (e) => {
    const newTitle = e.target.value;
    setTitle(newTitle);
  };

  const onDescriptionChange = (e) => {
    const newDesc = e.target.value;
    setDescription(newDesc);
  };
  const handleInputSelect = (input) => {
    const newInput = {
      type: input.type,
      id: randomId(),
      name: '',
      defaultValue: '',
      placeholder: input.placeholder,
      title: '',
      description: '',
      required: input.required,
    };

    if (
      input.type === 'select' ||
      input.type === 'multi-select' ||
      input.type === 'checkboxes'
    ) {
      newInput.choices = [];
    }

    if (input.type === 'multi-select' || input.type === 'checkboxes') {
      newInput.defaultValue = [];
    }

    setFormInputs((fields) => [...fields, newInput]);

    setInputModalOpen(false);
  };

  const handleInputChange = (newValue, item) => {
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          data.title = newValue;
          if (newValue && !data.name) {
            data.name = getMachineName(newValue);
          }

          return data;
        }

        return data;
      }),
    );
  };

  const handleDescriptionChange = (newValue, item) => {
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          data.description = newValue;
          return data;
        }

        return data;
      }),
    );
  };

  const handleRequiredChange = (checked, item) => {
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          data.required = checked;
          return data;
        }

        return data;
      }),
    );
  };

  const handleDeleteInput = (item) => {
    setFormInputs((fields) => fields.filter((task) => item.id !== task.id));
  };

  const onRowReorder = useCallback((dragIndex, hoverIndex) => {
    setFormInputs((fields) => {
      const newItems = [...fields];
      const dragItem = fields[dragIndex];
      newItems.splice(dragIndex, 1);
      newItems.splice(hoverIndex, 0, dragItem);

      return newItems;
    });
  }, []);

  const handleUploadMediaChange = (file) => {
    const extension = getFileExtension(file.name);
    if (
      acceptFileTypes &&
      !acceptFileTypes.includes(extension) &&
      (!file.type ||
        (!acceptFileTypes.includes(file.type) &&
          !acceptFileTypes?.includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'upload.errorInvalidFileType' }),
      );
    } else {
      setMedia(file);
    }

    return false;
  };

  const onRemoveMedia = () => {
    setMedia(null);
  };

  const onFinishDetails = (values) => {
    setFormInputs((fields) =>
      fields.map((data) => {
        if (selectedItem.id === data.id) {
          data = { ...data, ...values };
        }

        return data;
      }),
    );

    setOpenDetail(false);
  };

  const onBackClick = () => {
    if (step === 2) {
      setStep(step - 1);
    } else if (step === 3) {
      setStep(step - 1);
    } else if (step === 4) {
      setStep(step - 2);
    }

    setSkipped(false);
  };

  const onNextClick = () => {
    setStep(step + 1);
    if (step === 2) setSkipped(true);
  };

  const onSkipClick = () => {
    setSkipped(true);
    setStep(step + 1);
  };

  const onCreateClick = () => {
    const validInputs = formInputs.filter((input) => input.title);
    const schema = generateKbSchema(validInputs);

    addNewSpace({ ...payload, schema: JSON.stringify(schema) });
  };

  const onSubmitSuccess = (formData) => {
    const payload = {
      name: formData.name,
      description: formData.description || '',
      content_type: formData.content_type,
    };

    if (contentType === 'contact') {
      setFormInputs(CONTACT_SPACE_FIELDS);
      setPayload(payload);
      onNextClick();
    } else {
      addNewSpace(payload);
    }
  };

  const validInputs = formInputs.filter((input) => input.title);

  return (
    <Fragment>
      <Form
        onFinish={onSubmitSuccess}
        form={form}
        initialValues={{ content_type: contentType || 'general' }}
      >
        <AppMiniWindowBody>
          {step === 1 && (
            <StyledStepContainer>
              <StyledFormItem
                name="name"
                rules={[
                  {
                    required: true,
                    message: formatMessage({ id: 'validation.enterSpaceName' }),
                  },
                ]}
              >
                <StyledInput
                  placeholder={formatMessage({ id: 'space.spaceName' })}
                  variant="borderless"
                  onChange={onTitleChange}
                />
              </StyledFormItem>

              <StyledFormItem
                name="content_type"
                rules={[
                  {
                    required: true,
                    message: formatMessage({
                      id: 'validation.selectContentType',
                    }),
                  },
                ]}
              >
                <StyledSelect
                  placeholder={formatMessage({ id: 'form.contentType' })}
                  variant="borderless"
                  onChange={setContentType}
                >
                  {SPACE_CONTENT_TYPES?.map((role) => (
                    <Option key={role.id} value={role.id}>
                      {role.name}
                    </Option>
                  ))}
                </StyledSelect>
              </StyledFormItem>

              <StyledFormItem name="description" style={{ borderBottom: 0 }}>
                <StyledTextArea
                  placeholder={formatMessage({ id: 'form.description' })}
                  variant="borderless"
                  autoSize={{
                    minRows: 5,
                    maxRows: 50,
                  }}
                  onChange={onDescriptionChange}
                />
              </StyledFormItem>
            </StyledStepContainer>
          )}

          {step === 2 && (
            <StyledStepContainer>
              <Paragraph strong>
                {formatMessage({ id: 'knowledgeBase.addSchemaFields' })}
              </Paragraph>

              {formInputs.length > 0 && (
                <StyledList>
                  {formInputs.map((item, index) => (
                    <InputRow
                      key={item.id}
                      index={index}
                      item={item}
                      handleInputChange={handleInputChange}
                      handleDescriptionChange={handleDescriptionChange}
                      setSelectedItem={setSelectedItem}
                      setOpenDetail={setOpenDetail}
                      handleDeleteInput={handleDeleteInput}
                      handleRequiredChange={handleRequiredChange}
                      onRowReorder={onRowReorder}
                      contentType={contentType}
                    />
                  ))}
                </StyledList>
              )}

              <AppInputSelector
                open={inputModalOpen}
                onSelect={handleInputSelect}
                onOpenChange={setInputModalOpen}
              >
                <StyledStickyButton
                  type="primary"
                  size="small"
                  shape="round"
                  onClick={() => setInputModalOpen(!inputModalOpen)}
                  ghost
                >
                  <MdAdd fontSize={16} />
                  <span>{formatMessage({ id: 'common.addField' })}</span>
                </StyledStickyButton>
              </AppInputSelector>
            </StyledStepContainer>
          )}

          {step === 3 && (
            <StyledStepContainer>
              <StyledMediaWrapper>
                <StyledDragger
                  name="media"
                  accept={acceptFileTypes}
                  maxCount={1}
                  beforeUpload={handleUploadMediaChange}
                  onRemove={onRemoveMedia}
                  multiple={false}
                  fileList={media ? [media] : []}
                >
                  <Space direction="vertical" size={4}>
                    <Button
                      shape="circle"
                      icon={<MdArrowUpward fontSize={21} />}
                      css={`
                        margin-bottom: 8px;
                      `}
                    />

                    <Text>{formatMessage({ id: 'upload.dragText' })}</Text>
                  </Space>
                </StyledDragger>
              </StyledMediaWrapper>
            </StyledStepContainer>
          )}
        </AppMiniWindowBody>

        <AppMiniWindowFooter>
          <Row justify="space-between" align="middle">
            <Dropdown
              menu={{
                items: getLocalizedOptions(PERMISSION_TYPES, formatMessage),
                onClick: onShareChange,
                selectedKeys: currentPrivacy?.key,
              }}
              trigger={['click']}
              disabled={open}
            >
              <Link>
                <Space>
                  {currentPrivacy?.icon}
                  <span>{formatMessage({ id: currentPrivacy?.label })}</span>
                </Space>
              </Link>
            </Dropdown>

            {step > 1 ? (
              <Space>
                {step > 1 && (
                  <StyledButton
                    type="primary"
                    onClick={onBackClick}
                    loading={loading}
                    ghost
                  >
                    {formatMessage({ id: 'common.back' })}
                  </StyledButton>
                )}

                {isSkipped ? (
                  <StyledButton
                    type="primary"
                    onClick={onCreateClick}
                    loading={loading}
                  >
                    {formatMessage({ id: 'common.create' })}
                  </StyledButton>
                ) : (
                  <StyledButton
                    type="primary"
                    onClick={onNextClick}
                    disabled={validInputs.length === 0}
                    loading={loading}
                  >
                    {formatMessage({ id: 'common.next' })}
                  </StyledButton>
                )}

                {step > 1 && !isSkipped && contentType !== 'contact' && (
                  <StyledButton
                    type="primary"
                    onClick={onSkipClick}
                    loading={loading}
                    ghost
                  >
                    {formatMessage({ id: 'common.skip' })}
                  </StyledButton>
                )}
              </Space>
            ) : (
              <StyledButton type="primary" htmlType="submit" loading={loading}>
                {contentType === 'table' || contentType === 'contact'
                  ? formatMessage({ id: 'common.next' })
                  : formatMessage({ id: 'common.create' })}
              </StyledButton>
            )}
          </Row>
          <PostPermissionPopover
            open={open}
            currentSpace={currentSpace}
            setOpen={setOpen}
            userList={userList}
            setUserList={setUserList}
          />
        </AppMiniWindowFooter>
      </Form>

      <ManageDetails
        open={openDetail}
        onCancel={() => setOpenDetail(false)}
        onFinish={onFinishDetails}
        selectedItem={selectedItem}
        initialValues={selectedItem}
        contentType={contentType}
      />
    </Fragment>
  );
};

SpaceForm.propTypes = {
  content_type: PropTypes.string,
  onSaved: PropTypes.func,
};

export default SpaceForm;
