'use client';
import type {Components} from 'react-markdown';
import type {HTMLAttributes, ReactNode} from 'react';
import {Prism as SyntaxHighlighter} from 'react-syntax-highlighter';
import {vscDarkPlus} from 'react-syntax-highlighter/dist/esm/styles/prism';

type CodeProps = HTMLAttributes<HTMLElement> & {
  inline?: boolean;
  className?: string;
  children?: ReactNode;
};

export const getMarkdownComponents = (isUser: boolean): Components => ({
  code({inline, className, children, ...props}: CodeProps) {
    const match = /language-(\w+)/.exec(className || '');
    return !inline && match ? (
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={match[1]}
        PreTag="div"
        customStyle={{
          borderRadius: '8px',
          margin: '12px 0',
          fontSize: '14px',
        }}
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    ) : (
      <code
        style={{
          background: isUser
            ? 'rgba(255, 255, 255, 0.2)'
            : 'rgba(0, 0, 0, 0.05)',
          padding: '2px 6px',
          borderRadius: '4px',
          fontFamily: 'monospace',
          fontSize: '0.9em',
        }}
        className={className}
        {...props}
      >
        {children}
      </code>
    );
  },
  a({children, href, ...props}) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          color: isUser ? '#ffffff' : '#1890ff',
          textDecoration: 'underline',
          fontWeight: 500,
        }}
        {...props}
      >
        {children}
      </a>
    );
  },
  p({children}) {
    return <p style={{margin: 0, lineHeight: '1.6'}}>{children}</p>;
  },
  ul({children}) {
    return (
      <ul style={{marginLeft: '20px', marginTop: '8px', marginBottom: '8px'}}>
        {children}
      </ul>
    );
  },
  ol({children}) {
    return (
      <ol style={{marginLeft: '20px', marginTop: '8px', marginBottom: '8px'}}>
        {children}
      </ol>
    );
  },
  li({children}) {
    return <li style={{marginBottom: '4px'}}>{children}</li>;
  },
  h1({children}) {
    return (
      <h1 style={{fontSize: '1.5em', fontWeight: 700, margin: '12px 0 8px'}}>
        {children}
      </h1>
    );
  },
  h2({children}) {
    return (
      <h2 style={{fontSize: '1.3em', fontWeight: 700, margin: '12px 0 8px'}}>
        {children}
      </h2>
    );
  },
  h3({children}) {
    return (
      <h3 style={{fontSize: '1.1em', fontWeight: 600, margin: '10px 0 6px'}}>
        {children}
      </h3>
    );
  },
  blockquote({children}) {
    return (
      <blockquote
        style={{
          borderLeft: `4px solid ${isUser ? 'rgba(255,255,255,0.5)' : '#d9d9d9'}`,
          paddingLeft: '12px',
          margin: '12px 0',
          fontStyle: 'italic',
          color: isUser ? 'rgba(255,255,255,0.9)' : 'rgba(0,0,0,0.65)',
        }}
      >
        {children}
      </blockquote>
    );
  },
  table({children}) {
    return (
      <div style={{overflowX: 'auto', margin: '12px 0'}}>
        <table
          style={{
            borderCollapse: 'collapse',
            width: '100%',
            border: `1px solid ${isUser ? 'rgba(255,255,255,0.3)' : '#f0f0f0'}`,
          }}
        >
          {children}
        </table>
      </div>
    );
  },
  th({children}) {
    return (
      <th
        style={{
          border: `1px solid ${isUser ? 'rgba(255,255,255,0.3)' : '#f0f0f0'}`,
          padding: '8px 12px',
          background: isUser ? 'rgba(255,255,255,0.1)' : '#fafafa',
          fontWeight: 600,
          textAlign: 'left',
        }}
      >
        {children}
      </th>
    );
  },
  td({children}) {
    return (
      <td
        style={{
          border: `1px solid ${isUser ? 'rgba(255,255,255,0.3)' : '#f0f0f0'}`,
          padding: '8px 12px',
        }}
      >
        {children}
      </td>
    );
  },
});
