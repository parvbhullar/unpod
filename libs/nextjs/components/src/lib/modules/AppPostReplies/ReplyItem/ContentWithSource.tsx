import {Fragment, memo, useEffect, useRef, useState} from 'react';

import AppMarkdownViewer from '../../../third-party/AppMarkdownViewer';
import SourceDataView from './SourceDataView';
import AppDrawer from '../../../antd/AppDrawer';
import {StyledContentWrapper} from '../index.styled';

const regex = /\[\d\]+/g;

const ContentWithSource = ({reply}: { reply: any }) => {
  const contentRef = useRef<HTMLDivElement | null>(null);
  const [highlightedDoc, setHighlightedDoc] = useState<string | null>(null);

  useEffect(() => {
    if (contentRef.current) {
      const elements = contentRef.current.querySelectorAll('.document-handle');

      elements.forEach((element: Element) => {
        element.addEventListener('click', () => {
          const id = element.getAttribute('data-id');
          setHighlightedDoc(id);
        });
      });
    }

    return () => {
      const elements = document.querySelectorAll('.document-handle');

      elements.forEach((element: Element) => {
        element.removeEventListener('click', () => {
          setHighlightedDoc(null);
        });
      });
    };
  }, []);

  const replacer = (match: string) => {
    const matchValue = match.replace('[', '').replace(']', '');

    return `<span class="document-${matchValue} document-handle ${
      highlightedDoc === matchValue ? 'active' : ''
    }" data-id="${matchValue}" title="Reference ${match}"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 24 24" height="1em" width="1em"><path d="M18.3638 15.5355L16.9496 14.1213L18.3638 12.7071C20.3164 10.7545 20.3164 7.58866 18.3638 5.63604C16.4112 3.68341 13.2453 3.68341 11.2927 5.63604L9.87849 7.05025L8.46428 5.63604L9.87849 4.22182C12.6122 1.48815 17.0443 1.48815 19.778 4.22182C22.5117 6.95549 22.5117 11.3876 19.778 14.1213L18.3638 15.5355ZM15.5353 18.364L14.1211 19.7782C11.3875 22.5118 6.95531 22.5118 4.22164 19.7782C1.48797 17.0445 1.48797 12.6123 4.22164 9.87868L5.63585 8.46446L7.05007 9.87868L5.63585 11.2929C3.68323 13.2455 3.68323 16.4113 5.63585 18.364C7.58847 20.3166 10.7543 20.3166 12.7069 18.364L14.1211 16.9497L15.5353 18.364ZM14.8282 7.75736L16.2425 9.17157L9.17139 16.2426L7.75717 14.8284L14.8282 7.75736Z"></path></svg></span>`;
  };

  return (
    <Fragment>
      <StyledContentWrapper ref={contentRef}>
        <AppMarkdownViewer
          markdown={reply.data.content.replace(regex, replacer)}
        />
      </StyledContentWrapper>
      <AppDrawer
        title={reply.data.metadata.rephrased_query}
        open={highlightedDoc !== null}
        destroyOnHidden={true}
        onClose={() => setHighlightedDoc(null)}
        styles={{body: {padding: 0, position: 'relative'}}}
        width="60%"
      >
        <SourceDataView reply={reply} highlightedDoc={highlightedDoc}/>
      </AppDrawer>
    </Fragment>
  );
};

export default memo(ContentWithSource);
