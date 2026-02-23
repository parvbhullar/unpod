import React, {useEffect, useImperativeHandle, useState} from 'react';

import {usePaginatedDataApi} from '@unpod/providers';
import {tablePageSize} from '@unpod/constants';
import EmailListItem from './EmailListItem';
import GeneralListItem from './GeneralListItem';
import ContactListItem from './ContactListItem';
import AppList from '../../common/AppList';

const LIST_COMPONENTS = {
  email: EmailListItem,
  general: GeneralListItem,
  contact: ContactListItem,
};

const pageLimit = tablePageSize * 2;

const AppDocuments = ({
                        search,
                        records,
                        setRecords,
                        currentSpace,
                        activeDocument,
                        onDocumentClick,
                        allowSelection,
                        selectedDocs,
                        setSelectedDocs,
                        setDocsLoading,
                        spaceSchema,
                        activeTag,
                        // setSelectedDoc,
                        newSourceRef,
                        ref,
                      }) => {
  // const [addNewDoc, setAddNewDoc] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [
    {apiData, loading, isLoadingMore, hasMoreRecord, page},
    {setLoadingMore, setPage, setData, setQueryParams, updateInitialUrl},
  ] = usePaginatedDataApi(
    `knowledge_base/${currentSpace.token}/connector-data/`,
    [],
    {
      page_size: pageLimit,
    },
    false,
  );

  useEffect(() => {
    setRecords(apiData);
  }, [apiData]);

  useEffect(() => {
    if (currentSpace.token) {
      setQueryParams({page: 1, search: ''});
      updateInitialUrl(`knowledge_base/${currentSpace.token}/connector-data/`);
    }
  }, [currentSpace.token]);

  useEffect(() => {
    setQueryParams({
      page: 1,
      tag: activeTag === 'primary' ? '' : activeTag,
      search,
    });
  }, [activeTag, search]);

  useEffect(() => {
    setDocsLoading(loading && !isLoadingMore);
  }, [loading, isLoadingMore]);

  useImperativeHandle(ref, () => ({
    refreshData: () => {
      setPage(1);
    },
    resetEditDocument: () => {
      setSelectedDoc(null);
    },
  }));

  const onDocumentEdit = (doc) => {
    setSelectedDoc(doc);
    newSourceRef.current.editDocument(doc);
  };

  const onDocumentDelete = (doc) => {
    setRecords((prevData) =>
      prevData.filter((item) => item.document_id !== doc.document_id),
    );
  };

  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

  const ListItem = LIST_COMPONENTS[currentSpace.content_type];

  return (
    <AppList
      style={{
        height: 'calc(100vh - 172px)',
      }}
      data={apiData}
      loading={loading}
      footerProps={{
        loading: isLoadingMore,
      }}
      hasMoreRecord={hasMoreRecord}
      renderItem={(data, index) => (
        <ListItem
          key={index}
          data={data}
          currentSpace={currentSpace}
          onDocumentClick={onDocumentClick}
          activeDocument={activeDocument || selectedDoc}
          allowSelection={allowSelection}
          selectedDocs={selectedDocs}
          setSelectedDocs={setSelectedDocs}
          onDocumentEdit={onDocumentEdit}
          onDocumentDelete={onDocumentDelete}
          showTimeFrom
        />
      )}
      onEndReached={onEndReached}
    />
  );
};

AppDocuments.displayName = 'AppDocuments';

export default React.memo(AppDocuments);
