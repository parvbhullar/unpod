import type { MouseEvent } from 'react';
import { Fragment, memo, useEffect, useRef, useState } from 'react';

import { Button, Space, Tooltip, Typography } from 'antd';
import AppCopyToClipboard from '../../../../third-party/AppCopyToClipboard';
import { MdArrowBack, MdOutlineZoomIn } from 'react-icons/md';
import clsx from 'clsx';
import {
  capitalizedAllWords,
  convertMachineNameToName,
} from '@unpod/helpers/StringHelper';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { isJson } from '@unpod/helpers/GlobalHelper';
import AppMarkdownViewer from '../../../../third-party/AppMarkdownViewer';
import AppTable from '../../../../third-party/AppTable';
import {
  StyledCellContent,
  StyledContentContainer,
  StyledContentWrapper,
  StyledCopyWrapper,
  StyledDocWrapper,
  StyledFullContent,
  StyledIframeContainer,
  StyledRefRow,
  StyledRootContainer,
  StyledTitleContainer,
  StyledZoomContainer,
} from './index.styled';
import AppLink from '../../../../next/AppLink';
import AppJsonViewer from '../../../../third-party/AppJsonViewer';

const { Paragraph, Text, Title } = Typography;

type FrameData = { title?: string; content?: string; url?: string };
type SelectedCol = { title?: string; content?: string; url?: string };
type ReferenceData = {
  title?: string;
  data?: Array<{ title?: string; keyName?: string; content?: any }>;
};

const SourceDataView = ({
  reply,
  highlightedDoc,
}: {
  reply: any;
  highlightedDoc?: string | null;
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [columns, setColumns] = useState<any[]>([]);
  const [sourceData, setSourceData] = useState<any[]>([]);
  const [frameData, setFrameData] = useState<FrameData | null>(null);
  const [selectedCol, setSelectedCol] = useState<SelectedCol | null>(null);
  const [referenceData, setReferenceData] = useState<ReferenceData | null>(
    null,
  );
  const contentRef = useRef<HTMLDivElement | null>(null);
  const frameContentRef = useRef<HTMLDivElement | null>(null);
  const refContentRef = useRef<HTMLDivElement | null>(null);

  const onLinkClick = (
    e: MouseEvent,
    url?: string,
    title?: string,
    content?: string,
  ) => {
    e.preventDefault();
    e.stopPropagation();

    const validUrl = !!url && url.includes('http');

    if (validUrl) {
      getDataApi('media/pre-signed-url/', infoViewActionsContext, {
        url,
      })
        .then((res: any) => {
          if (url.includes('.pdf') || url.includes('.PDF')) {
            setFrameData({ title, content, url: res.data.url });
          } else {
            window.open(res.data.url, '_blank');
          }
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    } else {
      const highlightedContent = content || 'No content';
      setSelectedCol({ title, content: highlightedContent, url: '' });
    }
  };

  const onSourceUrlClick = (e: MouseEvent, url?: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!url) return;

    if (url.includes('unpodbackend.s3.amazonaws.com')) {
      getDataApi('media/pre-signed-url/', infoViewActionsContext, {
        url,
      })
        .then((res: any) => {
          window.open(res.data.url, '_blank');
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    } else {
      const newWindow = window.open(url, '_blank');
      newWindow?.focus();
    }
  };

  useEffect(() => {
    if (reply.data.metadata.ref_docs) {
      const cols = [
        {
          title:
            reply.data.metadata.ref_docs?.[0]?.source_type === 'gmail'
              ? 'URL'
              : 'Doc ID',
          dataIndex:
            reply.data.metadata.ref_docs?.[0]?.source_type === 'gmail'
              ? 'url'
              : 'document_id',
          key:
            reply.data.metadata.ref_docs?.[0]?.source_type === 'gmail'
              ? 'url'
              : 'document_id',
          dataType: 'string',
          render: (text: any, record: any) => (
            <StyledCellContent>
              <AppLink
                href={record.link || record.url}
                onClick={(e) =>
                  onLinkClick(
                    e,
                    record.link || record.url,
                    'Doc ID',
                    record.match_highlights?.toString(),
                  )
                }
              >
                {text}
              </AppLink>

              <StyledZoomContainer
                onClick={(e) =>
                  onLinkClick(
                    e,
                    record.link || record.url,
                    'Doc ID',
                    record.match_highlights?.toString(),
                  )
                }
              >
                <MdOutlineZoomIn fontSize={20} />
              </StyledZoomContainer>
            </StyledCellContent>
          ),
        },
      ];

      const colKeys: string[] = [];
      console.log('reply.data.metadata.ref_docs', reply.data.metadata.ref_docs);
      const data = reply.data.metadata.ref_docs.map((doc: any) => {
        if (doc.metadata) {
          console.log('doc.metadata', doc.metadata);
          Object.keys(doc.metadata).forEach((key: string) => {
            if (!colKeys.includes(key)) {
              colKeys.push(key);

              const title = capitalizedAllWords(
                convertMachineNameToName(key) || '',
              );

              cols.push({
                title: title,
                dataIndex: key,
                key: key,
                dataType: typeof doc.metadata[key],
                render: (text: any) => {
                  return (
                    <StyledCellContent>
                      <Paragraph
                        className="mb-0"
                        style={{ margin: 0, maxWidth: 300 }}
                        ellipsis={{
                          rows: 1,
                        }}
                      >
                        {text}
                      </Paragraph>

                      <StyledZoomContainer
                        onClick={() => setSelectedCol({ title, content: text })}
                      >
                        <MdOutlineZoomIn fontSize={20} />
                      </StyledZoomContainer>
                    </StyledCellContent>
                  );
                },
              });
            }
          });
        } else {
          const staticCols = [
            {
              title: 'Content',
              keyName: 'content',
              dataType: 'string',
            },
            /*{
              title: 'URL',
              keyName: 'semantic_identifier',
              dataType: 'string',
            },*/
          ];

          staticCols.forEach((col) => {
            if (!colKeys.includes(col.keyName)) {
              colKeys.push(col.keyName);

              cols.push({
                title: col.title,
                dataIndex: col.keyName,
                key: col.keyName,
                dataType: col.dataType,
                render: (text: any) => {
                  return (
                    <StyledCellContent>
                      <Paragraph
                        className="mb-0"
                        style={{ margin: 0, maxWidth: 300 }}
                        ellipsis={{
                          rows: 1,
                        }}
                      >
                        {text}
                      </Paragraph>

                      <StyledZoomContainer
                        onClick={() =>
                          setSelectedCol({ title: col.title, content: text })
                        }
                      >
                        <MdOutlineZoomIn fontSize={20} />
                      </StyledZoomContainer>
                    </StyledCellContent>
                  );
                },
              });
            }
          });
        }

        return {
          id: doc.db_doc_id || doc.document_id,
          document_id: doc.document_id,
          link: doc.link,
          url: doc.url,
          match_highlights: doc.match_highlights,
          ...doc,
          ...doc.metadata,
        };
      });

      setColumns(cols);
      setSourceData(data);
    }
  }, []);

  useEffect(() => {
    if (
      highlightedDoc &&
      reply?.data?.metadata?.ref_docs &&
      reply?.data?.metadata?.citation_num &&
      reply.data.metadata.citation_num[highlightedDoc]
    ) {
      const refDocumentId = reply.data.metadata.citation_num[highlightedDoc];
      const refDocData = reply.data.metadata.ref_docs.find(
        (doc: any) => doc.document_id === refDocumentId,
      );

      if (!refDocData) return;

      if (refDocData.metadata) {
        const data = [
          {
            title: 'Highlight',
            keyName: 'match_highlights',
            content: refDocData.match_highlights?.toString(),
          },
          {
            title: 'Content',
            keyName: 'content',
            content: refDocData.content,
          },
          ...Object.keys(refDocData.metadata)
            .filter((key) => key !== 'schema')
            .slice(0, 3)
            .map((key: string) => {
              return {
                title: capitalizedAllWords(convertMachineNameToName(key) || ''),
                keyName: key,
                content: refDocData.metadata[key],
              };
            }),
        ];

        setReferenceData({
          title: `Reference [${highlightedDoc}]`,
          data: data,
        });
      } else {
        const data = [
          {
            title: 'URL',
            keyName: 'url',
            content:
              refDocData.link ||
              refDocData.url ||
              refDocData.semantic_identifier,
          },
          {
            title: 'Content',
            keyName: 'content',
            content: refDocData.content,
          },
        ];

        setReferenceData({
          title: `Reference [${highlightedDoc}]`,
          data: data,
        });
      }
    }
  }, [highlightedDoc, reply.data.metadata]);

  const onBackClick = () => {
    contentRef.current?.classList.add('closing');

    setTimeout(() => {
      contentRef.current?.classList.remove('closing');
      setSelectedCol(null);
    }, 500);
  };

  const onPdfBackClick = () => {
    frameContentRef.current?.classList.add('closing');

    setTimeout(() => {
      frameContentRef.current?.classList.remove('closing');
      setFrameData(null);
    }, 500);
  };

  const onRefDataBackClick = () => {
    refContentRef.current?.classList.add('closing');

    setTimeout(() => {
      refContentRef.current?.classList.remove('closing');
      setReferenceData(null);
    }, 500);
  };

  const isJsonContent = !!selectedCol?.content && isJson(selectedCol.content);

  /*consoleLog(
    'highlightedDoc: ',
    highlightedDoc,
    reply,
    reply.data.metadata.citation_num[highlightedDoc],
    referenceData
  );*/
  console.log('frameData?.title', referenceData);
  return (
    <Fragment>
      <StyledRootContainer>
        {/*<pre>{JSON.stringify(reply.data.metadata, null, 4)}</pre>*/}

        <AppTable
          rowKey="id"
          columns={columns}
          dataSource={sourceData}
          size="middle"
          pagination={false}
        />
      </StyledRootContainer>

      <StyledFullContent
        ref={frameContentRef}
        className={clsx({ open: frameData })}
      >
        <StyledTitleContainer>
          <Space>
            <Tooltip title="Back">
              <Button
                type="text"
                size="small"
                shape="circle"
                onClick={onPdfBackClick}
              >
                <MdArrowBack fontSize={18} />
              </Button>
            </Tooltip>
            <Text strong>{frameData?.title}</Text>
          </Space>
        </StyledTitleContainer>

        <StyledDocWrapper>
          <Typography>
            <AppMarkdownViewer markdown={frameData?.content} />
          </Typography>

          {frameData?.url && (
            <StyledIframeContainer>
              <iframe
                src={frameData?.url}
                // width="100%"
                // height="100%"
                // frameBorder={0}
                style={{ border: 0, height: '100%', width: '100%' }}
              />
            </StyledIframeContainer>
          )}
        </StyledDocWrapper>
      </StyledFullContent>

      <StyledFullContent
        ref={contentRef}
        className={clsx({ open: selectedCol })}
      >
        <StyledTitleContainer>
          <Space>
            <Tooltip title="Back">
              <Button
                type="text"
                size="small"
                shape="circle"
                onClick={onBackClick}
              >
                <MdArrowBack fontSize={18} />
              </Button>
            </Tooltip>
            <Text strong>{selectedCol?.title}</Text>
          </Space>
        </StyledTitleContainer>

        <StyledContentContainer
          className={clsx({ 'json-content': isJsonContent })}
        >
          <StyledCopyWrapper>
            <AppCopyToClipboard
              text={
                isJsonContent
                  ? JSON.stringify(
                      JSON.parse(selectedCol?.content || '{}'),
                      null,
                      2,
                    )
                  : selectedCol?.content || ''
              }
              showToolTip
            />
          </StyledCopyWrapper>

          <StyledContentWrapper>
            {isJsonContent ? (
              <AppJsonViewer json={JSON.parse(selectedCol?.content || '{}')} />
            ) : (
              <AppMarkdownViewer markdown={selectedCol?.content} />
            )}
          </StyledContentWrapper>
        </StyledContentContainer>
      </StyledFullContent>

      <StyledFullContent
        ref={refContentRef}
        className={clsx('ref-content', { open: referenceData })}
      >
        <StyledTitleContainer>
          <Space>
            <Tooltip title="Back">
              <Button
                type="text"
                size="small"
                shape="circle"
                onClick={onRefDataBackClick}
              >
                <MdArrowBack fontSize={18} />
              </Button>
            </Tooltip>
            <Text strong>{referenceData?.title}</Text>
          </Space>
        </StyledTitleContainer>

        <StyledContentContainer>
          <StyledContentWrapper>
            {(referenceData?.data || []).map((item: any) =>
              item.content ? (
                <StyledRefRow
                  key={item.keyName}
                  className={clsx({ 'json-content': isJsonContent })}
                >
                  <StyledCopyWrapper>
                    <AppCopyToClipboard
                      text={
                        item.content && isJson(item.content)
                          ? JSON.stringify(JSON.parse(item.content), null, 2)
                          : item.content
                      }
                      showToolTip
                    />
                  </StyledCopyWrapper>

                  <Title level={4}>{item.title}: </Title>

                  <Typography>
                    {item.content && isJson(item.content) ? (
                      <AppJsonViewer json={JSON.parse(item?.content || '{}')} />
                    ) : (
                      <AppMarkdownViewer
                        markdown={item?.content}
                        components={{
                          a: ({ children, ...props }) => {
                            return (
                              <a
                                {...props}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) =>
                                  onSourceUrlClick(e, props.href || '')
                                }
                              >
                                {children}
                              </a>
                            );
                          },
                        }}
                      />
                    )}
                  </Typography>
                </StyledRefRow>
              ) : (
                <Fragment key={item.keyName} />
              ),
            )}
          </StyledContentWrapper>
        </StyledContentContainer>
      </StyledFullContent>
    </Fragment>
  );
};

export default memo(SourceDataView);
