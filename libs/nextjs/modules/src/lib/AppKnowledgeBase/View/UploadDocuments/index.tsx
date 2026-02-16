'use client';
import { useState } from 'react';
import {
  uploadDataApi,
  useInfoViewActionsContext,
  useInfoViewContext,
} from '@unpod/providers';
import { allowedFileTypes } from '@unpod/constants';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { Button, Form, Progress, Space, Typography } from 'antd';
import { MdArrowUpward } from 'react-icons/md';
import { StyledActions, StyledButton, StyledDragger } from './index.style';
import { DrawerForm } from '@unpod/components/antd';
import { useIntl } from 'react-intl';

type UploadDocumentsProps = {
  currentKb: any;
  onSaved?: () => void;
};

const UploadDocuments = ({ currentKb, onSaved }: UploadDocumentsProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { loading } = useInfoViewContext();
  const { formatMessage } = useIntl();

  const [uploadPercent, setUploadPercent] = useState(0);
  const [mediaList, setMediaList] = useState<any[]>([]);
  const acceptMediaTypes =
    allowedFileTypes[currentKb?.content_type] || allowedFileTypes['table'];

  const onSubmitSuccess = () => {
    const formData = new FormData();
    mediaList.forEach((file) => {
      formData.append('files', file);
    });

    uploadDataApi(
      `knowledge_base/${currentKb?.token}/`,
      infoViewActionsContext,
      formData,
      false,
      (progressEvent: { loaded: number; total?: number }) => {
        const total = progressEvent.total ?? 0;
        const percent = total
          ? Math.round((progressEvent.loaded * 100) / total)
          : 0;
        setUploadPercent(percent);
      },
    )
      .then(() => {
        setMediaList([]);
        onSaved?.();
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
      infoViewActionsContext.showError(
        formatMessage({ id: 'validation.fileTypeNotAllowed' }),
      );
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

  return (
    <DrawerForm onFinish={onSubmitSuccess} layout="vertical">
      {uploadPercent > 0 && uploadPercent < 100 ? (
        <Form.Item label={formatMessage({ id: 'common.uploading' })}>
          <Progress percent={uploadPercent} />
        </Form.Item>
      ) : (
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
            <Button shape="circle" icon={<MdArrowUpward fontSize={21} />} />

            <Typography.Text>
              {formatMessage({ id: 'knowledgeBase.dragFileToUpload' })}
            </Typography.Text>
          </Space>
        </StyledDragger>
      )}

      <StyledActions>
        <StyledButton
          type="primary"
          shape="round"
          htmlType="submit"
          block
          loading={loading}
          disabled={!mediaList.length}
        >
          {formatMessage({ id: 'common.upload' })}
        </StyledButton>
      </StyledActions>
    </DrawerForm>
  );
};

export default UploadDocuments;
