import {Fragment, useEffect} from 'react';
import {Spin} from 'antd';
import {useAppSpaceActionsContext, useAppSpaceContext, useGetDataApi,} from '@unpod/providers';
import {getStringFromHtml} from '@unpod/helpers/GlobalHelper';
import DocumentFooter from '../DocumentFooter';
import DocumentView from './DocumentView';
import {StyledDetailsRoot, StyledRow} from './index.styled';
import type {Document} from '@unpod/constants/types';

const GeneralDocView = () => {
  const {currentSpace, activeDocument} = useAppSpaceContext();
  const {setActiveTab} = useAppSpaceActionsContext();

  const [{apiData, loading}, {setData, updateInitialUrl}] = useGetDataApi(
    `knowledge_base/${currentSpace?.token}/connector-doc-data/${activeDocument?.document_id}/`,
    {data: undefined as Document | undefined},
    {},
    false,
  ) as [
    { apiData: { data?: Document }; loading: boolean },
    { setData: (value: any) => void; updateInitialUrl: (url: string) => void },
  ];

  useEffect(() => {
    if (currentSpace?.token && activeDocument?.document_id) {
      setData({data: undefined});
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
    if (activeDocument) {
      onSuggestionsClick('');
    }
  }, [activeDocument]);

  const onSuggestionsClick = (suggestion: string) => {
    const description = getStringFromHtml(
      activeDocument?.description || apiData?.data?.content || '',
    );
    void description;

    // newConvRef.current?.setContext(suggestion, context);//TODO: enable this when suggestions are needed XXXXXXXX
    if (suggestion) setActiveTab('conversations');
  };

  return (
    <StyledDetailsRoot>
      {loading ? (
        <StyledRow align="middle" justify="center">
          <Spin/>
        </StyledRow>
      ) : (
        <Fragment>
          <DocumentView document={apiData?.data || ({} as Document)}/>
          <DocumentFooter onSuggestionsClick={onSuggestionsClick}/>
        </Fragment>
      )}
    </StyledDetailsRoot>
  );
};

export default GeneralDocView;
