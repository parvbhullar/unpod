import {Fragment, useState} from 'react';

import {Button, Collapse, Form, Progress, Space, Typography} from 'antd';
import {MdAdd, MdArrowUpward, MdDelete} from 'react-icons/md';
import {allowedFileTypes} from '@unpod/constants';
import {
  postDataApi,
  uploadDataApi,
  useAppSpaceContext,
  useInfoViewActionsContext,
  useInfoViewContext,
} from '@unpod/providers';
import {getFileExtension} from '@unpod/helpers/FileHelper';
import AppInput from '../../../antd/AppInput';
import {StyledActions, StyledContainer, StyledDragger, StyledItemRow, StyledLabel, StyledRoot,} from './index.styled';
import {getMachineName} from '@unpod/helpers/StringHelper';
import {useIntl} from 'react-intl';

const {Item, List, useForm} = Form;
const {Text} = Typography;
const {Panel} = Collapse;

const mainDocExtension = allowedFileTypes['document'];
const acceptMediaTypes = allowedFileTypes['document'];

type AddNewSourceProps = {
  setAddNewDoc?: (open: boolean) => void;
  onDocumentAdded?: (data: any) => void;
};

const AddNewSource = ({setAddNewDoc, onDocumentAdded}: AddNewSourceProps) => {
  const {currentSpace} = useAppSpaceContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const {loading} = useInfoViewContext();
  const [form] = useForm();
  const {formatMessage} = useIntl();

  const [uploadPercent, setUploadPercent] = useState(0);
  const [contentFile, setContentFile] = useState<any | null>(null);
  // const [allowAttachment, setAllowAttachments] = useState(false);
  const [attachments, setAttachments] = useState<any[]>([]);

  const uploadAttachments = (
    files: any[],
    callbackFun: (files: any[]) => void,
  ) => {
    const formData = new FormData();
    formData.append('object_type', 'post');
    files.forEach((file: any) => {
      formData.append('files', file);
    });

    uploadDataApi(
      `media/upload-multiple/`,
      infoViewActionsContext,
      formData,
      false,
      (progressEvent) => {
        if (!progressEvent.total) return;
        setUploadPercent(
          Math.round((progressEvent.loaded * 100) / progressEvent.total),
        );
      },
    )
      .then((res: any) => {
        callbackFun(res.data);
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const handleBeforeUploadContentFile = (file: any) => {
    const extension = getFileExtension(file.name)?.toLowerCase();
    if (
      mainDocExtension &&
      !mainDocExtension.includes(extension) &&
      (!file.type ||
        (!mainDocExtension.includes(file.type) &&
          !mainDocExtension?.includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(
        formatMessage({id: 'validation.fileTypeNotAllowed'}),
      );
    } else {
      setContentFile(file);
    }

    return false;
  };

  const onRemoveContentFile = () => {
    setContentFile(null);
  };

  const handleBeforeUploadFile = (file: any) => {
    const extension = getFileExtension(file.name)?.toLowerCase();
    if (
      acceptMediaTypes &&
      !acceptMediaTypes.includes(extension) &&
      (!file.type ||
        (!acceptMediaTypes.includes(file.type) &&
          !acceptMediaTypes?.includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(
        formatMessage({id: 'validation.fileTypeNotAllowed'}),
      );
    } else {
      setAttachments((prevState) => [...prevState, file]);
    }

    return false;
  };

  const onRemoveFile = (file: any) => {
    const index = attachments.indexOf(file);
    const newFileList = attachments.slice();
    newFileList.splice(index, 1);
    setAttachments(newFileList);
  };

  const addToSource = (payload: any) => {
    postDataApi(
      `knowledge_base/${currentSpace?.token}/connector-doc-data/`,
      infoViewActionsContext,
      payload,
    )
      .then((response: any) => {
        if (response.data.failed === 0) {
          infoViewActionsContext.showMessage(response.message);
          onDocumentAdded?.(response?.data);
        } else {
          const failedErrors = response.data.errors.map(
            (item: any) => item.error,
          );
          infoViewActionsContext.showError(failedErrors.join(', '));
        }
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const onSubmitSuccess = (values: any) => {
    const metadata = (values.items || []).reduce((acc: any, item: any) => {
      acc[item.option_key] = item.option_value;
      return acc;
    }, {});

    uploadAttachments([contentFile], (files: any[]) => {
      const payload = {
        metadata: {
          ...metadata,
          source_type: 'manual',
        },
        files: [
          {
            ...files[0],
            media_relation: 'content',
          },
        ],
      };

      if (attachments?.length) {
        uploadAttachments(attachments, (files: any[]) => {
          payload.files = [
            ...payload.files,
            ...files.map((file) => ({
              ...file,
              media_relation: 'attachment',
            })),
          ];

          addToSource(payload);
        });
      } else {
        addToSource(payload);
      }
    });
  };

  return (
    <StyledRoot>
      <StyledContainer>
        <Form
          form={form}
          onFinish={onSubmitSuccess}
          layout="vertical"
          initialValues={{
            items: [],
          }}
        >
          {uploadPercent > 0 && uploadPercent < 100 ? (
            <Item label={formatMessage({id: 'common.uploading'})}>
              <Progress percent={uploadPercent}/>
            </Item>
          ) : (
            <Fragment>
              <StyledLabel>
                {formatMessage({id: 'addNewSource.uploadDocument'})}
              </StyledLabel>
              <Item
                name="file"
                rules={[
                  {
                    required: true,
                    message: formatMessage({id: 'validation.chooseFile'}),
                  },
                ]}
                required={false}
              >
                <StyledDragger
                  name="content_file"
                  accept={mainDocExtension}
                  maxCount={5}
                  beforeUpload={handleBeforeUploadContentFile}
                  onRemove={onRemoveContentFile}
                  fileList={contentFile ? [contentFile] : []}
                  multiple={false}
                >
                  <Space orientation="vertical" size={4}>
                    <Button
                      shape="circle"
                      icon={<MdArrowUpward fontSize={21}/>}
                      style={{marginBottom: 8}}
                    />

                    <Text>{formatMessage({id: 'upload.dragDropFiles'})}</Text>
                  </Space>
                </StyledDragger>
              </Item>

              <Collapse expandIconPosition="end" style={{marginBottom: 24}}>
                <Panel
                  header={formatMessage({id: 'addNewSource.advancedOptions'})}
                  key="1"
                >
                  <StyledLabel>
                    {formatMessage({id: 'addNewSource.metadataOptions'})}
                  </StyledLabel>
                  <List name="items">
                    {(fields, {add, remove}) => (
                      <>
                        {fields.map(({key, name, ...restField}) => (
                          <StyledItemRow key={key}>
                            <Item
                              {...restField}
                              name={[name, 'option_key']}
                              rules={[
                                {
                                  required: true,
                                  message: formatMessage({
                                    id: 'validation.fieldRequired',
                                  }),
                                },
                              ]}
                            >
                              <AppInput
                                placeholder={formatMessage({
                                  id: 'addNewSource.optionKey',
                                })}
                                onBlur={(event: any) => {
                                  const configKey = event.target.value;

                                  if (configKey) {
                                    const formattedKey =
                                      getMachineName(configKey);
                                    const items = form.getFieldValue('items');
                                    items[name].option_key = formattedKey;
                                    form.setFieldsValue({
                                      items: items,
                                    });
                                  }
                                }}
                                asterisk
                              />
                            </Item>

                            <Item
                              {...restField}
                              name={[name, 'option_value']}
                              rules={[
                                {
                                  required: true,
                                  message: formatMessage({
                                    id: 'validation.fieldRequired',
                                  }),
                                },
                              ]}
                            >
                              <AppInput
                                placeholder={formatMessage({
                                  id: 'addNewSource.optionValue',
                                })}
                                asterisk
                              />
                            </Item>

                            <Item>
                              <Button
                                type="primary"
                                onClick={() => remove(name)}
                                icon={<MdDelete fontSize={18}/>}
                                danger
                                ghost
                              />
                            </Item>
                          </StyledItemRow>
                        ))}

                        <Item>
                          <Button
                            type="dashed"
                            onClick={() => add()}
                            block
                            icon={<MdAdd/>}
                          >
                            {formatMessage({id: 'common.addField'})}
                          </Button>
                        </Item>
                      </>
                    )}
                  </List>

                  <StyledLabel>
                    {formatMessage({id: 'addNewSource.additionalFiles'})}
                  </StyledLabel>
                  <Item name="files" className="mb-0">
                    <StyledDragger
                      name="attachments"
                      accept={mainDocExtension}
                      maxCount={5}
                      beforeUpload={handleBeforeUploadFile}
                      onRemove={onRemoveFile}
                      fileList={attachments}
                      multiple
                    >
                      <Space orientation="vertical" size={4}>
                        <Button
                          shape="circle"
                          icon={<MdArrowUpward fontSize={21}/>}
                          style={{marginBottom: 8}}
                        />

                        <Text>
                          {formatMessage({id: 'upload.dragDropFiles'})}
                        </Text>
                      </Space>
                    </StyledDragger>
                  </Item>
                </Panel>
              </Collapse>

              <StyledActions>
                {setAddNewDoc && (
                  <Button onClick={() => setAddNewDoc(false)} block>
                    {formatMessage({id: 'common.cancel'})}
                  </Button>
                )}

                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  block
                >
                  {formatMessage({id: 'common.save'})}
                </Button>
              </StyledActions>
            </Fragment>
          )}
        </Form>
      </StyledContainer>
    </StyledRoot>
  );
};

export default AddNewSource;
