import { useEffect, useMemo, useState } from 'react';
import { AppFileUpload } from '@unpod/components/antd';
import { getColumns } from './columns';
import { Modal } from 'antd';
import {
  deleteDataApi,
  uploadPostDataApi,
  useGetDataApi,
  useInfoViewActionsContext,
  useInfoViewContext,
} from '@unpod/providers';
import { StyledHeaderWrapper, StyledRoot } from './index.styled';
import AppTable from '@unpod/components/third-party/AppTable';
import { requiredDocs } from './constants';
import { useIntl } from 'react-intl';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';
import type { RcFile } from 'antd/es/upload';

const ACCEPT_TYPES = ['pdf', 'jpg', 'png'];
const AppTableAny = AppTable as any;

const getUploadedDocuments = (data: any[] = []) => {
  if (!data || data.length === 0) return requiredDocs;

  const uploadedDocs: Record<string, any> = {};
  data.forEach((item) => {
    // Match by both document_type (uppercase) and key (lowercase)
    // to ensure compatibility with different API response formats
    uploadedDocs[item.document_type] = item;
    if (item.key) {
      uploadedDocs[item.key] = item;
    }
  });

  return requiredDocs.map((doc) => {
    // Try matching by both document_type and key
    const uploadedDoc =
      uploadedDocs[doc.document_type] || uploadedDocs[doc.key];

    if (uploadedDoc) {
      // Normalize status to always be a string key, never an object
      let normalizedStatus = uploadedDoc?.status || 'review';
      if (typeof normalizedStatus === 'object') {
        // If API returns status as an object, extract the key or use a default
        normalizedStatus = normalizedStatus?.key || 'review';
      }

      return {
        ...doc,
        ...uploadedDoc,
        status: normalizedStatus,
      };
    } else {
      return doc;
    }
  });
};

type DocumentsProps = {
  sipBridge?: any;
};

const Documents = ({ sipBridge }: DocumentsProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const infoViewContext = useInfoViewContext();
  const [selectedDoc, setSelectedDoc] = useState<any>(null);
  const { formatMessage } = useIntl();

  const [{ apiData, loading }, { setQueryParams, setData }] = useGetDataApi(
    'documents/',
    {
      data: [],
    },
    {
      module_type: 'bridge',
      module_object_id: sipBridge?.slug,
    },
    false,
  ) as any;

  useEffect(() => {
    if (sipBridge) {
      setQueryParams({
        module_type: 'bridge',
        module_object_id: sipBridge.slug,
      });
    } else {
      setData({ data: [] });
    }
  }, [sipBridge]);

  // Upload a file for a specific document type
  const handleUpload = (file: File | RcFile) => {
    if (!file || !selectedDoc?.key) {
      return;
    }
    // File size check
    if (file.size > 5 * 1024 * 1024) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'bridge.fileSizeError' }),
      );
      return;
    }
    // File type check
    const extension = file?.name?.split('.')?.pop()?.toLowerCase();
    if (extension && !ACCEPT_TYPES.includes(extension)) {
      return;
    }
    const formData = new FormData();
    formData.append('module_type', 'bridge');
    formData.append('module_object_id', sipBridge.slug);
    // Use the 'key' field (lowercase snake_case) instead of 'document_type' (uppercase)
    formData.append('document_type', selectedDoc.document_type);
    formData.append('file', file);

    uploadPostDataApi('documents/', infoViewActionsContext, formData)
      .then((response: any) => {
        setSelectedDoc(null);
        infoViewActionsContext.showMessage(
          response.message || formatMessage({ id: 'bridge.uploaded' }),
        );
        setData({ data: [...apiData.data, response.data] });
      })
      .catch((error: any) => {
        // Handle validation errors from API
        let errorMessage = formatMessage({ id: 'bridge.uploadFailed' });

        if (error.message) {
          // If error.message is an object (validation errors), extract readable message
          if (typeof error.message === 'object') {
            const errorMessages = Object.entries(error.message)
              .map(([field, messages]) => {
                const messageArray = Array.isArray(messages)
                  ? messages
                  : [messages];
                return messageArray.join(', ');
              })
              .filter(Boolean);

            if (errorMessages.length > 0) {
              errorMessage = errorMessages.join('; ');
            }
          } else if (typeof error.message === 'string') {
            errorMessage = error.message;
          }
        }

        infoViewActionsContext.showError(errorMessage);
      });
  };

  const onDelete = (id: string | number) => {
    if (!id) return;
    deleteDataApi(`/documents/${id}/`, infoViewActionsContext)
      .then((data: any) => {
        infoViewActionsContext.showMessage(data.message || 'File deleted');
        setData({ data: apiData.data.filter((item: any) => item.id !== id) });
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(
          error?.message || formatMessage({ id: 'bridge.fileDeleted' }),
        );
      });
  };

  const uploadedDocuments = useMemo(() => {
    const mergedDocs = getUploadedDocuments(apiData?.data);
    return getLocalizedOptions(mergedDocs, formatMessage) as any;
  }, [apiData?.data, formatMessage]);

  return (
    <StyledRoot>
      <StyledHeaderWrapper>
        {formatMessage({ id: 'bridge.requiredDocuments' })}
      </StyledHeaderWrapper>

      <AppTableAny
        rowKey="key"
        fullHeight
        loading={loading || infoViewContext.loading}
        columns={getColumns(onDelete, setSelectedDoc, formatMessage) as any}
        dataSource={uploadedDocuments}
        pagination={false}
      />

      <Modal
        title={
          selectedDoc?.title || formatMessage({ id: 'bridge.uploadDocument' })
        }
        centered={true}
        open={!!selectedDoc}
        onCancel={() => setSelectedDoc(null)}
        footer={null}
        width={600}
        loading={infoViewContext.loading}
      >
        <AppFileUpload
          acceptTypes={ACCEPT_TYPES.join(',')}
          files={[]}
          setFiles={(fileArr) => {
            const file = Array.isArray(fileArr) ? fileArr[0] : fileArr;
            if (file) handleUpload(file);
          }}
          multiple={false}
        />
      </Modal>
    </StyledRoot>
  );
};

export default Documents;
