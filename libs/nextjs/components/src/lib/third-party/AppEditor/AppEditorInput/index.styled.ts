import styled from 'styled-components';

export const StyledAppEditor = styled.div`
  .ql-editor,
  .ql-container {
    font-size: 14px;
    font-family: ${({theme}) => theme.font.family};
    border: 0 none;
    padding: 0;
    color: ${({theme}) => theme.palette.text.content};
    line-height: 1.6;
  }

  .ql-container {
    .ql-editor.ql-blank::before {
      left: 0;
      right: 0;
      font-style: normal;
      color: rgba(0, 0, 0, 0.35);
    }

    &.ql-bubble {
      .ql-tooltip {
        border-radius: ${({theme}) => theme.radius.base}px;
        z-index: 99999;
      }
    }
  }

  .ql-editor {
    .ql-custom-hr {
      height: 0;
      margin: 16px 0 10px 0;
      border: 1px solid ${({theme}) => theme.border.color};
    }
  }
`;

export const StyledToolbar = styled.div`
  display: none;
  font-size: 14px !important;
  font-family: ${({theme}) => theme.font.family} !important;

  &.ql-toolbar {
    display: block;
    border-radius: ${({theme}) => theme.radius.base}px;

    &.theme-snow {
      position: sticky;
      bottom: 0;
      top: auto;
      background-color: ${({theme}) => theme.palette.background.default};
      margin-top: 16px;
    }

    .ql-bubble & .ql-picker-options {
      border-radius: ${({theme}) => theme.radius.base}px;
      box-shadow: 0 0 6px rgba(255, 255, 255, 0.25);
      margin-top: auto;
      margin-bottom: -1px;
      top: auto;
      bottom: 100%;
    }
  }
`;
