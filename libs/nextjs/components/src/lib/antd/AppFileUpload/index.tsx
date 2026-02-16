import React, { ReactNode } from 'react';
import { Button, Form, Typography, Upload } from 'antd';
import { RiFileTextLine } from 'react-icons/ri';
import {
  StyledInnerContainer,
  StyledUploadContainer,
  StyledUploadWrapper,
} from './index.styled';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { useInfoViewActionsContext } from '@unpod/providers';
import { useIntl } from 'react-intl';
import type { RcFile, UploadProps } from 'antd/es/upload';

const { Dragger } = Upload;
const { Paragraph } = Typography;
const { Item } = Form;


type UploadFileLike = File | RcFile;

export type FileUploadProps = {
  acceptTypes?: string; // e.g. ".pdf,.docx" OR "image/*"
  files: UploadFileLike | UploadFileLike[] | null;
  setFiles: (files: UploadFileLike | UploadFileLike[] | null) => void;
  children?: ReactNode;
  multiple?: boolean;
  maxFileCount?: number;
  label?: string;};

export const FileUpload: React.FC<FileUploadProps> = ({
  acceptTypes,
  files,
  setFiles,
  children,
  multiple = false,
  maxFileCount = 10,
  label,
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();

  const handleUploadChange: UploadProps['beforeUpload'] = (file, fileList) => {
    const extension = getFileExtension(file.name);
    if (
      acceptTypes &&
      !acceptTypes.includes(extension) &&
      (!file.type || !acceptTypes.includes(file.type))
    ) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'validation.fileTypeNotAllowed' }),
      );
      setFiles(null);
      return false;
    }
    if (multiple) {
      setFiles(
        fileList.slice(0, maxFileCount) as RcFile[],
      );
    } else {
      setFiles(file);
    }
    return false;
  };

  const hasFileSelected = () => {
    return (
      (Array.isArray(files) && !!files.length) ||
      (files && !Array.isArray(files) && files.name)
    );
  };


  return (
    <>
      {children}
      <Item
        rules={[
          {
            required: !hasFileSelected(),
            message: `${formatMessage({ id: 'upload.fileType' })} ${acceptTypes}`,
          },
        ]}
      >
        <StyledUploadWrapper>
          {label && <Paragraph strong>{label}</Paragraph>}

          <StyledUploadContainer>
            <Dragger
              accept={acceptTypes}
              multiple={multiple}
              maxCount={maxFileCount}
              beforeUpload={handleUploadChange}
              showUploadList={false}
              fileList={[]}
            >
              <StyledInnerContainer>
                <RiFileTextLine fontSize={36} />
                <Paragraph>
                  {formatMessage({ id: 'upload.dragDropFiles' })}
                </Paragraph>
                <Button type="primary" style={{ height: 36 }}>
                  {formatMessage({ id: 'common.chooseFile' })}
                </Button>
              </StyledInnerContainer>
            </Dragger>
          </StyledUploadContainer>
        </StyledUploadWrapper>
      </Item>
    </>
  );
};

export default FileUpload;
