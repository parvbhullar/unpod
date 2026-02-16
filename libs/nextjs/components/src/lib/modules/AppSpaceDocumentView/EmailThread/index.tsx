import { useEffect, useState } from 'react';
import { Collapse, Spin } from 'antd';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useFetchDataApi,
} from '@unpod/providers';
import { getStringFromHtml } from '@unpod/helpers/GlobalHelper';
import AppMarkdownViewer from '../../../third-party/AppMarkdownViewer';
import DocumentFooter from '../DocumentFooter';
import EmailItem from './EmailItem';
import {
  StyledDetailsRoot,
  StyledRow,
  StyledSummaryContent,
} from './index.styled';
import { useIntl } from 'react-intl';

type EmailItemData = {
  document_id?: string | number;
  body?: string;
  [key: string]: any;
};

const EmailThread = () => {
  const { currentSpace, activeDocument } = useAppSpaceContext();
  const { setActiveTab } = useAppSpaceActionsContext();
  const [summary, setSummary] = useState('');
  const { formatMessage } = useIntl();

  const [{ apiData, loading }, { setData, setPage, updateInitialUrl }] =
    useFetchDataApi(
      `knowledge_base/${currentSpace?.token}/connector-doc-data/${activeDocument?.document_id}/`,
      [],
      {},
      false,
    ) as [
      { apiData: EmailItemData[]; loading: boolean },
      {
        setData: (value: any) => void;
        setPage: (page: number) => void;
        updateInitialUrl: (url: string) => void;
      },
    ];

  useEffect(() => {
    if (currentSpace?.token && activeDocument?.document_id) {
      setSummary('');
      setData([]);
      setPage(1);
      updateInitialUrl(
        `knowledge_base/${currentSpace.token}/connector-doc-data/${activeDocument.document_id}/`,
      );
    }
  }, [
    currentSpace?.token,
    activeDocument?.document_id,
    setData,
    setPage,
    updateInitialUrl,
  ]);

  useEffect(() => {
    if (apiData.length > 0) {
      onSuggestionsClick('');
    }
  }, [apiData]);

  const onSuggestionsClick = (suggestion: string) => {
    const description = apiData.map(
      (email) => getStringFromHtml(email.body || '') + '',
    );
    void description;

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

      {summary && !loading && (
        <StyledSummaryContent>
          <Collapse
            size="small"
            expandIconPosition="right"
            defaultActiveKey={['summary']}
            items={[
              {
                key: 'summary',
                label: formatMessage({ id: 'common.summary' }),
                children: <AppMarkdownViewer markdown={summary} />,
              },
            ]}
          />
        </StyledSummaryContent>
      )}

      {apiData?.map((email, index) => (
        <EmailItem
          key={email.document_id ?? index}
          email={email}
          isFirst={index === 0}
          setSummary={setSummary}
        />
      ))}

      {apiData.length > 0 && !loading && (
        <DocumentFooter
          onSuggestionsClick={onSuggestionsClick}
          summary={summary}
        />
      )}
    </StyledDetailsRoot>
  );
};

export default EmailThread;
