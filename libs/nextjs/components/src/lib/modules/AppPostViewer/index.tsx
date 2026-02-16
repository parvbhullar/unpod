import { Fragment } from 'react';

import styled from 'styled-components';
import { GlobalTheme } from '@unpod/constants';
// import ReactQuill from 'react-quill';

export const StyledAppPostViewerWrapper = styled.div`
  max-width: 990px;
  padding-right: 30px;

  .ql-editor,
  .ql-container {
    font-size: 14px;
    font-family: ${({ theme }: { theme: GlobalTheme }) => theme.font.family};
    border: 0 none;
    padding: 0;
    color: ${({ theme }: { theme: GlobalTheme }) => theme.palette.text.content};
    line-height: 1.6;
  }

  .ql-editor {
    .ql-custom-hr {
      height: 0;
      margin: 16px 0 10px 0;
      border: 1px solid
        ${({ theme }: { theme: GlobalTheme }) => theme.border.color};
    }
  }
`;

const AppPostViewer = ({ content }: { content?: string }) => {
  return content ? (
    <StyledAppPostViewerWrapper className="app-post-viewer">
      {/*<ReactQuill readOnly={true} value={content} theme="bubble" />*/}
      {content}
    </StyledAppPostViewerWrapper>
  ) : (
    <Fragment />
  );
};

export default AppPostViewer;

