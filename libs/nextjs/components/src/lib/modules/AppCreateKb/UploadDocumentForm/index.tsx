import {Button, Divider, Flex, Space, Typography} from 'antd';
import {allowedFileTypes} from '@unpod/constants';
import {getFileExtension} from '@unpod/helpers/FileHelper';
import {StyledDragger, StyledMediaWrapper} from '../index.styled';
import {MdArrowUpward, MdDownload, MdEdit} from 'react-icons/md';
import {useInfoViewActionsContext} from '@unpod/providers';
import {AppHeaderButton} from '../../../common/AppPageHeader';
import {useIntl} from 'react-intl';

const {Text, Link, Title, Paragraph} = Typography;

type UploadDocumentFormProps = {
  setMedia: (file: any | null) => void;
  media?: any | null;
  contentType?: string;
  onEditSchema?: () => void;
};

const UploadDocumentForm = ({
                              setMedia,
                              media,
                              contentType,
                              onEditSchema,
                            }: UploadDocumentFormProps) => {
  const {formatMessage} = useIntl();
  const infoViewActionsContext = useInfoViewActionsContext();
  const acceptFileTypes = allowedFileTypes[contentType || 'table'];

  const handleUploadMediaChange = (file: any) => {
    const extension = getFileExtension(file.name);
    if (
      acceptFileTypes &&
      !acceptFileTypes.includes(extension) &&
      (!file.type ||
        (!acceptFileTypes.includes(file.type) &&
          !acceptFileTypes?.includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(
        formatMessage({id: 'upload.errorInvalidFileType'}),
      );
    } else {
      setMedia(file);
    }

    return false;
  };

  const onRemoveMedia = () => {
    setMedia(null);
  };

  return (
    <StyledMediaWrapper>
      <div style={{marginBottom: 24}}>
        <Title level={4} style={{marginBottom: 8}}>
          {formatMessage({id: 'upload.titleImportContacts'})}
        </Title>

        <Paragraph type="secondary" style={{marginBottom: 0, fontSize: 14}}>
          {formatMessage({id: 'upload.descriptionImportContacts'})}
        </Paragraph>
      </div>

      <StyledDragger
        name="media"
        accept={acceptFileTypes}
        maxCount={1}
        beforeUpload={handleUploadMediaChange}
        onRemove={onRemoveMedia}
        multiple={false}
        fileList={media ? [media] : []}
      >
        <Space orientation="vertical" size={8} align="center">
          <Button
            shape="circle"
            icon={<MdArrowUpward fontSize={21}/>}
            style={{marginBottom: 8}}
          />

          <Text strong>{formatMessage({id: 'upload.dragText'})}</Text>

          <Text type="secondary" style={{fontSize: 12}}>
            {formatMessage(
              {id: 'upload.supportedFormat'},
              {formats: acceptFileTypes},
            )}
          </Text>

          <Link
            href="/sample-files/sample-template.csv"
            download="sample-template.csv"
            style={{fontSize: 13}}
          >
            <MdDownload style={{verticalAlign: 'middle', marginRight: 4}}/>
            {formatMessage({id: 'upload.downloadSample'})}
          </Link>
        </Space>
      </StyledDragger>

      {onEditSchema && (
        <>
          <Divider plain>{formatMessage({id: 'common.or'})}</Divider>

          <Flex style={{marginBottom: 16}}>
            <AppHeaderButton
              type="primary"
              ghost
              icon={<MdEdit/>}
              onClick={onEditSchema}
            >
              {formatMessage({id: 'upload.editSchema'})}
            </AppHeaderButton>
          </Flex>
        </>
      )}
    </StyledMediaWrapper>
  );
};

export default UploadDocumentForm;
