
import React, { ReactNode } from 'react';
import AppCopyToClipboard from '../AppCopyToClipboard';
import ReactMarkdown, { Components } from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeKatex from 'rehype-katex';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { base16AteliersulphurpoolLight } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { useTheme } from 'styled-components';
import { StyledContainer, StyledCopyWrapper, StyledRoot } from './index.styled';

type CodeCopyBtnProps = {
  children: ReactNode;
  textToCopy: string;
};

const CodeCopyBtn: React.FC<CodeCopyBtnProps> = ({ children, textToCopy }) => {
  return (
    <StyledContainer>
      <StyledCopyWrapper>
        <AppCopyToClipboard text={textToCopy} showToolTip />
      </StyledCopyWrapper>
      {children}
    </StyledContainer>
  );
};

type AppMarkdownViewerProps = {
  markdown?: string;
  children?: string;
  components?: Partial<Components>;
};

const AppMarkdownViewer: React.FC<AppMarkdownViewerProps> = ({
  markdown,
  children,
  components,
}) => {
  const theme = useTheme();

  return (
    <StyledRoot>
      <ReactMarkdown
        rehypePlugins={[rehypeRaw, rehypeKatex]}
        remarkPlugins={[remarkGfm, remarkMath]}
        components={{
          h1: 'h2',
          a: ({ node, inline, children, ...props }: any) => {
            return (
              <a {...props} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            );
          },
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');

            return !inline && match ? (
              <CodeCopyBtn textToCopy={String(children).replace(/\n$/, '')}>
                <SyntaxHighlighter
                  style={base16AteliersulphurpoolLight}
                  PreTag="div"
                  language={match[1]}
                  customStyle={{
                    borderRadius: (theme as any).radius.base,
                    margin: 0,
                  }}
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              </CodeCopyBtn>
            ) : (
              <CodeCopyBtn textToCopy={String(children).replace(/\n$/, '')}>
                <code className={className} {...props}>
                  {children}
                </code>
              </CodeCopyBtn>
            );
          },
          ...components,
        }}
      >
        {children || markdown}
      </ReactMarkdown>
    </StyledRoot>
  );
};

export default AppMarkdownViewer;
