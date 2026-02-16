import { Fragment, useEffect, useState } from 'react';

import { Button, Col, Form, Progress, Space, Typography } from 'antd';
import { MdArrowUpward } from 'react-icons/md';
import { allowedFileTypes } from '@unpod/constants';
import {
  getDataApi,
  postDataApi,
  putDataApi,
  uploadDataApi,
  useAppSpaceContext,
  useInfoViewActionsContext,
  useInfoViewContext,
} from '@unpod/providers';
import {
  capitalizedAllWords,
  convertMachineNameToName,
} from '@unpod/helpers/StringHelper';
import { fileDownload, getFileExtension } from '@unpod/helpers/FileHelper';
import AppInput from '../../../antd/AppInput';
import AppGridContainer from '../../../antd/AppGridContainer';
import {
  StyledActions,
  StyledContainer,
  StyledDragger,
  StyledRoot,
  StyledTabs,
} from './index.styled';
import { AppPopover } from '../../../antd';
import { useIntl } from 'react-intl';

const { Item, useForm } = Form;
const { Text } = Typography;

type AddContactDocProps = {
  selectedDoc?: any;
  onCancel: () => void;
  onDocumentAdded?: (data: any) => void;};

const AddContactDoc = ({
  selectedDoc,
  onCancel,
  onDocumentAdded,
}: AddContactDocProps) => {
  const { currentSpace, spaceSchema } = useAppSpaceContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { loading } = useInfoViewContext();
  const { formatMessage } = useIntl();
  const [form] = useForm();
  const [downloadLoading, setDownloadLoading] = useState({
    csv: false,
    xlsx: false,
  });

  const [activeTab, setActiveTab] = useState(
    selectedDoc ? 'add-manually' : 'import',
  );
  const [uploadPercent, setUploadPercent] = useState(0);
  const [mediaList, setMediaList] = useState<any[]>([]);
  const schema = (spaceSchema as {
    properties?: Record<string, { title?: string }>;
    required?: string[];
  }) || { properties: {}, required: [] };

  const acceptMediaTypes =
    allowedFileTypes[currentSpace?.content_type || 'table'] ||
    allowedFileTypes['table'];

  useEffect(() => {
    if (selectedDoc) {
      setActiveTab('add-manually');
      form.setFieldsValue(selectedDoc);
    } else {
      form.resetFields();
    }
  }, [selectedDoc, form]);

  const onSubmitSuccess = () => {
    const formData = new FormData();
    mediaList.forEach((file: any) => {
      formData.append('files', file);
    });

    uploadDataApi(
      `knowledge_base/${currentSpace?.token}/`,
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
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        setMediaList([]);
        onDocumentAdded?.(response?.data);
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };
  const handleUploadMediaChange = (file: any) => {
    const extension = getFileExtension(file.name)?.toLowerCase();
    if (
      acceptMediaTypes &&
      !acceptMediaTypes.includes(extension) &&
      (!file.type ||
        (!acceptMediaTypes.includes(file.type) &&
          !acceptMediaTypes?.includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(`File type is now allowed`);
    } else {
      setMediaList((prevState) => [...prevState, file]);
    }

    return false;
  };

  const onRemoveMedia = (file: any) => {
    const index = mediaList.indexOf(file);
    const newFileList = mediaList.slice();
    newFileList.splice(index, 1);
    setMediaList(newFileList);
  };

  const onSubmitDocument = (values: Record<string, any>) => {
    const spaceToken = currentSpace?.token;
    if (!spaceToken) {
      infoViewActionsContext.showError('Space not found');
      return;
    }

    if (selectedDoc) {
      putDataApi(
        `knowledge_base/${spaceToken}/connector-doc-data/${selectedDoc.document_id}/`,
        infoViewActionsContext,
        values,
      )
        .then((response: any) => {
          infoViewActionsContext.showMessage(response.message);
          onDocumentAdded?.(response?.data);
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    } else {
      postDataApi(
        `knowledge_base/${spaceToken}/connector-doc-data/`,
        infoViewActionsContext,
        values,
      )
        .then((response: any) => {
          infoViewActionsContext.showMessage(response.message);
          onDocumentAdded?.(response?.data);
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    }
  };

  const onSchemaDownload = (type: 'csv' | 'xlsx') => {
    setDownloadLoading((prev) => ({ ...prev, [type]: true }));
    getDataApi(
      `spaces/${currentSpace?.slug}/schema-download/?type=${type}`,
      infoViewActionsContext,
      {},
      false,
      {},
      'blob',
    )
      .then((res: any) => {
        const mime =
          type === 'csv'
            ? 'text/csv'
            : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

        fileDownload(
          res,
          `${formatMessage({ id: 'schema.schema' })}.${type}`,
          mime,
        );
      })
      .catch((err: any) => {
        infoViewActionsContext.showError(err.message);
      })
      .finally(() => {
        setDownloadLoading((prev) => ({ ...prev, [type]: false }));
      });
  };

  return (
    <StyledRoot>
      <StyledTabs
        hideAdd
        centered={false}
        type="card"
        size="small"
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            label: formatMessage({ id: 'addContactDoc.import' }),
            key: 'import',
          },
          {
            label: formatMessage({ id: 'addContactDoc.addManually' }),
            key: 'add-manually',
          },
        ]}
      />

      <StyledContainer>
        {activeTab === 'import' ? (
          <Form onFinish={onSubmitSuccess} layout="vertical">
            {uploadPercent > 0 && uploadPercent < 100 ? (
              <Item label={formatMessage({ id: 'addContactDoc.uploading' })}>
                <Progress percent={uploadPercent} />
              </Item>
            ) : (
              <Fragment>
                <Item
                  name="files"
                  rules={[
                    {
                      required: true,
                      message: formatMessage({
                        id: 'addContactDoc.selectFile',
                      }),
                    },
                  ]}
                >
                  <StyledDragger
                    name="media"
                    accept={acceptMediaTypes}
                    maxCount={5}
                    beforeUpload={handleUploadMediaChange}
                    onRemove={onRemoveMedia}
                    fileList={mediaList}
                    multiple
                  >
                    <Space orientation="vertical" size={4}>
                      <Button
                        shape="circle"
                        icon={<MdArrowUpward fontSize={21} />}
                        style={{ marginBottom: 8 }}
                      />

                      <Text>
                        {formatMessage({ id: 'addContactDoc.dragDropOrClick' })}
                      </Text>

                      <AppPopover
                        placement="bottom"
                        trigger="click"
                        content={
                          <StyledActions>
                            <Button
                              type="link"
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                onSchemaDownload('csv');
                              }}
                              loading={downloadLoading.csv}
                            >
                              {formatMessage({
                                id: 'addContactDoc.downloadCsv',
                              })}
                            </Button>
                            <Button
                              type="link"
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                onSchemaDownload('xlsx');
                              }}
                              loading={downloadLoading.xlsx}
                            >
                              {formatMessage({
                                id: 'addContactDoc.downloadXlsx',
                              })}
                            </Button>
                          </StyledActions>
                        }
                      >
                        <Button
                          type="link"
                          size="small"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {formatMessage({
                            id: 'addContactDoc.downloadSchema',
                          })}
                        </Button>
                      </AppPopover>
                    </Space>
                  </StyledDragger>
                </Item>

                <StyledActions>
                  <Button onClick={onCancel} block>
                    {formatMessage({ id: 'common.cancel' })}
                  </Button>

                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    block
                  >
                    {formatMessage({ id: 'common.save' })}
                  </Button>
                </StyledActions>
              </Fragment>
            )}
          </Form>
        ) : (
          <Form onFinish={onSubmitDocument} form={form}>
            <AppGridContainer gutter={12}>
              {/*<pre>{JSON.stringify(spaceSchema, null, 2)}</pre>*/}
              {schema?.properties &&
                Object.keys(schema?.properties).map((field) => {
                  const input = schema.properties?.[field];
                  const placeholder =
                    input?.title ||
                    capitalizedAllWords(convertMachineNameToName(field) || '');

                  return (
                    <Col key={field} sm={24} md={12}>
                      <Item
                        name={field}
                        rules={[
                          {
                            required: schema?.required?.includes(field),
                            message: formatMessage(
                              {
                                id: 'validation.inputField',
                              },
                              { field: field },
                            ),
                          },
                        ]}
                      >
                        <AppInput placeholder={placeholder} />
                      </Item>
                    </Col>
                  );
                })}
            </AppGridContainer>

            <StyledActions>
              <Button onClick={onCancel} block>
                Cancel
              </Button>

              <Button type="primary" htmlType="submit" loading={loading} block>
                {formatMessage({ id: 'common.save' })}
              </Button>
            </StyledActions>
          </Form>
        )}
      </StyledContainer>
    </StyledRoot>
  );
};

export default AddContactDoc;
