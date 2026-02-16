import styled from 'styled-components';
import { Typography } from 'antd';
import Editor from '@monaco-editor/react';
import { rgba } from 'polished';

const { Paragraph } = Typography;

export const StyledPlaceholder = styled(Paragraph)`
  position: absolute;
  display: ${({ hidden }) => (hidden ? 'none' : 'block')};
  white-space: pre-wrap;
  top: 16px;
  left: 50px;
  // font-size: 16px;
  font-family: Consolas, 'Courier New', monospace;
  pointer-events: none;
  user-select: none;
`;

export const StyledEditor = styled(Editor)`
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  padding-block: 16px;
  background-color: ${({ theme }) => theme.palette.background.default};

  &:focus-within {
    border-color: ${({ theme }) => theme.palette.primary};
  }

  & .monaco-editor {
    // padding-block: 16px;
    // height: 30vh;
    // min-height: 30vh;
  }

  & .view-overlays.focused,
  & .margin-view-overlays.focused {
    & .current-line {
      background-color: ${({ theme }) => rgba(theme.palette.primary, 0.16)};
    }
  }
`;
