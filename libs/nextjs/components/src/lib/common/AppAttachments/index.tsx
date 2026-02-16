import React from 'react';
import { Typography } from 'antd';
import {
  MdOutlineDownloadForOffline,
  MdOutlineFilePresent,
} from 'react-icons/md';
import {
  StyledActionsWrapper,
  StyledAttachment,
  StyledRoot,
} from './index.styled';
import {
  BsFilePdf,
  BsFileText,
  BsFiletypeCsv,
  BsFiletypeDoc,
  BsFiletypeDocx,
  BsFiletypeXls,
  BsFiletypeXlsx,
} from 'react-icons/bs';

const ICON_SIZE = 24;
const FILE_ICONS: Record<string, React.ReactNode> = {
  pdf: <BsFilePdf fontSize={ICON_SIZE} />,
  txt: <BsFileText fontSize={ICON_SIZE} />,
  xls: <BsFiletypeXls fontSize={ICON_SIZE} />,
  xlsx: <BsFiletypeXlsx fontSize={ICON_SIZE} />,
  csv: <BsFiletypeCsv fontSize={ICON_SIZE} />,
  docx: <BsFiletypeDocx fontSize={ICON_SIZE} />,
  doc: <BsFiletypeDoc fontSize={ICON_SIZE} />,
};

const DefaultFileIcon = () => <MdOutlineFilePresent fontSize={ICON_SIZE} />;

type Attachment = {
  file_type: string;
  [key: string]: unknown;};

type AppAttachmentsProps = {
  attachments: Attachment[];
  onDownload?: (item: Attachment) => void;};

const AppAttachments: React.FC<AppAttachmentsProps> = ({
  attachments,
  onDownload,
}) => {
  return (
    <StyledRoot>
      {attachments.map((item, index) => (
        <StyledAttachment key={index}>
          {FILE_ICONS[item.file_type.toLowerCase()] || <DefaultFileIcon />}
          <Typography.Text className="file-extension-name">
            {item.file_type.toUpperCase()}
          </Typography.Text>

          {onDownload && (
            <StyledActionsWrapper>
              <MdOutlineDownloadForOffline
                fontSize={24}
                className="download-btn"
                onClick={() => onDownload(item)}
              />
            </StyledActionsWrapper>
          )}
        </StyledAttachment>
      ))}
    </StyledRoot>
  );
};

export default AppAttachments;
