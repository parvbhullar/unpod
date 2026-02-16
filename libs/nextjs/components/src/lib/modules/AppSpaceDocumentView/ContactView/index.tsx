import { Fragment, useEffect } from 'react';
import { Spin } from 'antd';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useGetDataApi,
} from '@unpod/providers';
import ContactViewCard from './ContactViewCard';
import { StyledDetailsRoot, StyledRow } from './index.styled';

type ContactData = Record<string, any>;

const ContactView = () => {
  const { currentSpace, spaceSchema, activeDocument } = useAppSpaceContext();
  const { setActiveTab, setSelectedDocs } = useAppSpaceActionsContext();

  const [{ apiData, loading }, { setData, updateInitialUrl }] = useGetDataApi(
    `knowledge_base/${currentSpace?.token}/connector-doc-data/${activeDocument?.document_id}/`,
    { data: {} as ContactData },
    {},
    false,
    ({ data }: { data: ContactData }) => {
      if (data.document_id) {
        setSelectedDocs([String(data.document_id)]);
      }
    },
  ) as [
    { apiData: { data?: ContactData }; loading: boolean },
    { setData: (value: any) => void; updateInitialUrl: (url: string) => void },
  ];

  useEffect(() => {
    if (currentSpace?.token && activeDocument?.document_id) {
      setData({ data: {} as ContactData });
      updateInitialUrl(
        `knowledge_base/${currentSpace.token}/connector-doc-data/${activeDocument.document_id}/`,
      );
    }
  }, [
    currentSpace?.token,
    activeDocument?.document_id,
    setData,
    updateInitialUrl,
  ]);

  useEffect(() => {
    if (apiData.data) {
      onSuggestionsClick('');
    }
  }, [apiData]);

  const onSuggestionsClick = (suggestion: string) => {
    // Placeholder for future suggestions handling.

    // newConvRef.current?.setContext(suggestion, context);//TODO: enable this when suggestions are needed XXXXXXXX
    if (suggestion) setActiveTab('conversations');
  };

  return (
    <StyledDetailsRoot>
      {loading && (
        <StyledRow align="middle" justify="center">
          <Spin />
        </StyledRow>
      )}

      {apiData.data && !loading && (
        <Fragment>
          <ContactViewCard
            contact={apiData.data || {}}
            spaceSchema={spaceSchema}
          />

          {/* {process.env.isDevMode === 'yes' && (
            <DocumentFooter hideSuggestions>
              <AppSpaceContactCall
                idKey="document_id"
                space={currentSpace}
                documents={[apiData.data]}
                onFinishSchedule={() => {
                  setActiveTab('tasks');
                }}
                hideExport
              />
            </DocumentFooter>
          )}*/}
        </Fragment>
      )}
    </StyledDetailsRoot>
  );
};

export default ContactView;
