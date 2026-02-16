'use client';
import React, {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';
import PropTypes from 'prop-types';
import { uploadDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { useOrgActionContext } from '@unpod/providers';
import {
  allowedFileTypes,
  CONTACT_SPACE_FIELDS,
  contentTypeData,
  PERMISSION_TYPES,
} from '@unpod/constants';
import { Button, Dropdown, Form, Row, Select, Space, Typography } from 'antd';
import { MdAdd, MdArrowUpward } from 'react-icons/md';
import _debounce from 'lodash/debounce';
import { getDraftData, saveDraftData } from '@unpod/helpers/DraftHelper';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { getMachineName } from '@unpod/helpers/StringHelper';
import { randomId } from '@unpod/helpers/GlobalHelper';
import { generateKbSchema } from '@unpod/helpers/AppKbHelper';
import PostPermissionPopover from '../../common/PermissionPopover/PostPermissionPopover';
import {
  AppMiniWindowBody,
  AppMiniWindowFooter,
} from '../../common/AppMiniWindow';
import AppInputSelector from '../../antd/AppInputSelector';
import InputRow from '../AppKbSchemaManager/InputRow';
import ManageDetails from '../AppKbSchemaManager/ManageDetails';
import {
  StyledButton,
  StyledContainer,
  StyledDragger,
  StyledFormItem,
  StyledInput,
  StyledList,
  StyledMediaWrapper,
  StyledSelect,
  StyledStickyButton,
  StyledTextArea,
} from './index.styled';
import { useIntl } from 'react-intl';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';

const { Link, Paragraph, Text } = Typography;

const AddForm = ({ onSaved }) => {
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
  const {formatMessage} = useIntl();

  const [inputModalOpen, setInputModalOpen] = useState(false);
  const [formInputs, setFormInputs] = useState([]);
  const [openDetail, setOpenDetail] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [media, setMedia] = useState(null);

  const [dataFetched, setDataFetched] = useState(false);
  const debounceFn = useCallback(_debounce(saveDraftData, 2000), []);

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
  }, [title, description, contentType, privacyType, userList, dataFetched]);

  useEffect(() => {
    if (!dataFetched) {
      const draftData = getDraftData(`save-kb`);

      if (draftData) {
        setTitle(draftData.title);
        setDescription(draftData.description);
        setContentType(draftData.content_type);
        setPrivacyType(draftData.privacy);
        setUserList(draftData.users);

        form.setFieldsValue({
          name: draftData.title,
          description: draftData.description,
          content_type: draftData.content_type,
        });
      }

      setTimeout(() => {
        setDataFetched(true);
      }, 1000);
    }
  }, [dataFetched]);

  useEffect(() => {
    setCurrentPrivacy(
      PERMISSION_TYPES.find((item) => item.key === privacyType)
    );
  }, [privacyType]);

  const acceptFileTypes = useMemo(() => {
    return allowedFileTypes[contentType || 'table'];
  }, [contentType]);

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
      })
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
      })
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
      })
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
        formatMessage({ id: 'validation.fileTypeNotAllowed' }),
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
      })
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

    createKnowledgeBase({ ...payload, schema: JSON.stringify(schema) });
  };

  const createKnowledgeBase = (payload) => {
    setLoading(true);
    const formData = new FormData();
    for (const key in payload) {
      formData.append(key, payload[key]);
    }

    if (media) formData.append('files', media);

    formData.append('space_type', 'knowledge_base');
    formData.append('privacy_type', privacyType);

    if (privacyType === 'shared') {
      formData.append('invite_list', JSON.stringify(userList));
    } else {
      formData.append('invite_list', JSON.stringify([]));
    }

    uploadDataApi('spaces/', infoViewActionsContext, formData)
      .then((data) => {
        setLoading(false);
        localStorage.removeItem(`save-kb`);
        infoViewActionsContext.showMessage(data.message);
        if (onSaved) onSaved(data);
      })
      .catch((response) => {
        setLoading(false);
        infoViewActionsContext.showError(response.message);
      });
  };

  const onSubmitSuccess = (formData) => {
    const payload = {
      name: formData.name,
      description: formData.description || '',
      content_type: formData.content_type,
    };

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

  const validInputs = formInputs.filter((input) => input.title);

  return (
    <Fragment>
      <Form onFinish={onSubmitSuccess} form={form}>
        <AppMiniWindowBody>
          {step === 1 && (
            <StyledContainer>
              <StyledFormItem
                name="name"
                rules={[
                  {
                    required: true,
                    message: formatMessage({
                      id: 'validation.enterKnowledgeBase',
                    }),
                  },
                ]}
              >
                <StyledInput
                  placeholder={formatMessage({ id: 'knowledgeBase.pageTitle' })}
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
                  {contentTypeData?.map((role) => (
                    <Select.Option key={role.id} value={role.id}>
                      {formatMessage({ id: role.name })}
                    </Select.Option>
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
            </StyledContainer>
          )}

          {step === 2 && (
            <StyledContainer>
              <Paragraph strong>
                {formatMessage({ id: 'knowledgeBase.addSchemaFields' })}
              </Paragraph>

              {formInputs.length > 0 && (
                <Fragment>
                  {/*<StyledRowHeader>
                    <StyledRow gutter={12}>
                      <Col sm={10}>
                        <Text>Parameter</Text>
                      </Col>
                      <Col sm={9}>
                        <Text>Description</Text>
                      </Col>
                      <Col sm={5}>
                        <StyledActionLabel>Actions</StyledActionLabel>
                      </Col>
                    </StyledRow>
                  </StyledRowHeader>*/}

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
                </Fragment>
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
            </StyledContainer>
          )}

          {step === 3 && (
            <StyledContainer>
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
            </StyledContainer>
          )}

          {/*{step === 4 && (
            <StyledContainer>
              <StyledMediaWrapper>
                <StyledDragger
                  name="media"
                  accept={acceptMediaTypes}
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

                    <Text>Drag your file to upload</Text>
                  </Space>
                </StyledDragger>
              </StyledMediaWrapper>
            </StyledContainer>
          )}*/}
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
                  <span>
                    {currentPrivacy?.label
                      ? formatMessage({ id: currentPrivacy.label })
                      : ''}
                  </span>
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

AddForm.propTypes = {
  onSaved: PropTypes.func,
};

export default AddForm;
