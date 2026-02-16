import { Fragment, useEffect, useState } from 'react';
import AddWidget from './AddWidget';
import AddNewSource from '@unpod/components/modules/AppDocuments/AddNewSource';
import { StyledContainer, StyledInnerContainer } from './index.styled';
import AddContactDoc from '@unpod/components/modules/AppDocuments/AddContactDoc';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';

const DocumentView = () => {
  const [addNewDoc, setAddNewDoc] = useState(false);
  const { setActiveDocument, setDocumentMode, connectorActions } =
    useAppSpaceActionsContext();

  const { currentSpace, documentMode, activeDocument, connectorData } =
    useAppSpaceContext();
  const AddNewSourceAny = AddNewSource as any;

  useEffect(() => {
    if (documentMode === 'add') {
      setAddNewDoc(true);
      setActiveDocument(null);
    } else if (documentMode === 'edit') {
      setAddNewDoc(true);
    } else if (documentMode === 'view') {
      setAddNewDoc(false);
    }
  }, [activeDocument, documentMode]);

  const onCancel = () => {
    setDocumentMode('view');
    setAddNewDoc(false);
  };

  const onDocumentAdded = (doc: any) => {
    setDocumentMode('view');
    if (activeDocument?.document_id) {
      const updatedData = (connectorData?.apiData || []).map((data: any) =>
        data.document_id === doc.document_id ? doc : data,
      );
      connectorActions?.setData?.(updatedData);
      setAddNewDoc(false);
      setActiveDocument(doc);
    } else {
      connectorActions?.reCallAPI?.();
      setAddNewDoc(false);
      // setActiveDocument(doc);
    }
  };

  return (
    <Fragment>
      {addNewDoc ? (
        <StyledContainer>
          <StyledInnerContainer>
            {currentSpace?.content_type === 'contact' ? (
              <AddContactDoc
                selectedDoc={activeDocument}
                onCancel={onCancel}
                onDocumentAdded={onDocumentAdded}
              />
            ) : (
              <AddNewSourceAny
                currentSpace={currentSpace}
                setAddNewDoc={setAddNewDoc}
                onDocumentAdded={onDocumentAdded}
              />
            )}
          </StyledInnerContainer>
        </StyledContainer>
      ) : (
        <AddWidget onClick={() => setAddNewDoc(true)} />
      )}
    </Fragment>
  );
};

DocumentView.displayName = 'DocumentView';

export default DocumentView;
