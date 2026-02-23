'use client';
import styled from 'styled-components';
import {
  FileExcelOutlined,
  FileImageOutlined,
  FileOutlined,
  FilePdfOutlined,
  FilePptOutlined,
  FileTextOutlined,
  FileWordOutlined,
  FileZipOutlined,
} from '@ant-design/icons';

type FileContainerProps = {
  $hasContent?: boolean;
};

type FileUserProps = {
  $isUser?: boolean;
};

type FileIconWrapperProps = {
  $color?: string;
};

type FileAttachmentItem = {
  media_id?: string | number;
  name?: string;
  media_type?: string;
  media_url?: string;
  url?: string;
  size?: number;
};

type FileAttachmentProps = {
  files?: FileAttachmentItem[];
  isUser?: boolean;
  hasContent?: boolean;
};

const FileContainer = styled.div<FileContainerProps>`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: ${(props) => (props.$hasContent ? '8px' : '0')};
`;

const ImageGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
  max-width: 400px;
`;

const ImagePreview = styled.a<FileUserProps>`
  position: relative;
  border-radius: 6px;
  overflow: hidden;
  background: transparent;
  border: 1px solid
    ${(props) => (props.$isUser ? 'rgba(255,255,255,0.15)' : '#e0e0e0')};
  transition: all 0.2s ease;
  display: block;
  cursor: pointer;

  &:hover {
    border-color: ${(props) =>
  props.$isUser ? 'rgba(255,255,255,0.3)' : '#c0c0c0'};
  }

  img {
    display: block;
    width: 100%;
    height: auto;
    max-height: 160px;
    object-fit: cover;
  }
`;

const FileList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`;

const FileCard = styled.a<FileUserProps>`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  background: transparent;
  border: 1px solid
    ${(props) => (props.$isUser ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)')};
  text-decoration: none;
  color: inherit;
  transition: all 0.2s ease;
  cursor: pointer;
  max-width: 320px;

  &:hover {
    background: ${(props) =>
  props.$isUser ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)'};
    border-color: ${(props) =>
  props.$isUser ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.15)'};
  }
`;

const FileIconWrapper = styled.div<FileIconWrapperProps>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  background: ${(props) => props.$color || '#6366f1'}15;
  color: ${(props) => props.$color || '#6366f1'};
  font-size: 14px;
  flex-shrink: 0;
`;

const FileInfo = styled.div`
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: 6px;
`;

const FileName = styled.div<FileUserProps>`
  font-weight: 500;
  font-size: 13px;
  color: ${(props) =>
  props.$isUser ? props.theme.palette.text.primary : '#111827'};
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const FileSize = styled.div<FileUserProps>`
  font-size: 11px;
  font-weight: 400;
  color: ${(props) =>
  props.$isUser ? props.theme.palette.text.secondary : '#6b7280'};
  white-space: nowrap;
  flex-shrink: 0;
`;

const getFileIcon = (fileName?: string, fileType?: string) => {
  const ext = fileName?.split('.').pop()?.toLowerCase() ?? '';
  const type = fileType?.toLowerCase();

  if (
    type?.startsWith('image/') ||
    type === 'image' ||
    ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)
  ) {
    return {icon: FileImageOutlined, color: '#10b981'};
  }
  if (type === 'application/pdf' || ext === 'pdf') {
    return {icon: FilePdfOutlined, color: '#ef4444'};
  }
  if (
    type?.includes('word') ||
    type?.includes('msword') ||
    ['doc', 'docx'].includes(ext)
  ) {
    return {icon: FileWordOutlined, color: '#3b82f6'};
  }
  if (
    type?.includes('excel') ||
    type?.includes('spreadsheet') ||
    ['xls', 'xlsx', 'csv'].includes(ext)
  ) {
    return {icon: FileExcelOutlined, color: '#10b981'};
  }
  if (
    type?.includes('presentation') ||
    type?.includes('powerpoint') ||
    ['ppt', 'pptx'].includes(ext)
  ) {
    return {icon: FilePptOutlined, color: '#f59e0b'};
  }
  if (type?.startsWith('text/') || ['txt', 'md', 'json', 'xml'].includes(ext)) {
    return {icon: FileTextOutlined, color: '#06b6d4'};
  }
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
    return {icon: FileZipOutlined, color: '#8b5cf6'};
  }
  return {icon: FileOutlined, color: '#6b7280'};
};

const formatFileSize = (bytes?: number) => {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
};

const isImageFile = (fileName?: string, mediaType?: string) => {
  const name = fileName ?? '';
  return (
    mediaType === 'image' ||
    mediaType?.startsWith('image/') ||
    /\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(name)
  );
};

const FileAttachment = ({files, isUser, hasContent}: FileAttachmentProps) => {
  if (!files || files.length === 0) return null;

  const images = files.filter((file) =>
    isImageFile(file.name, file.media_type),
  );
  const otherFiles = files.filter(
    (file) => !isImageFile(file.name, file.media_type),
  );

  return (
    <FileContainer $hasContent={hasContent}>
      {images.length > 0 && (
        <ImageGrid>
          {images.map((file, index) => {
            const imageUrl = file.media_url || file.url;
            const fileName = file.name || 'Image';

            return (
              <ImagePreview
                key={file.media_id || index}
                href={imageUrl}
                target="_blank"
                rel="noopener noreferrer"
                $isUser={isUser}
              >
                <img src={imageUrl} alt={fileName}/>
              </ImagePreview>
            );
          })}
        </ImageGrid>
      )}

      {otherFiles.length > 0 && (
        <FileList>
          {otherFiles.map((file, index) => {
            const fileName = file.name || 'Attachment';
            const fileUrl = file.media_url || file.url;
            const {icon: IconComponent, color} = getFileIcon(
              fileName,
              file.media_type,
            );
            const fileSize = formatFileSize(file.size);

            return (
              <FileCard
                key={file.media_id || index}
                href={fileUrl}
                target="_blank"
                rel="noopener noreferrer"
                $isUser={isUser}
              >
                <FileIconWrapper $color={color}>
                  <IconComponent/>
                </FileIconWrapper>
                <FileInfo>
                  <FileName $isUser={isUser}>{fileName}</FileName>
                  {fileSize && <FileSize $isUser={isUser}>{fileSize}</FileSize>}
                </FileInfo>
              </FileCard>
            );
          })}
        </FileList>
      )}
    </FileContainer>
  );
};

export default FileAttachment;
