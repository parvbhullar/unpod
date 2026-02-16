import styled from 'styled-components';
import { rgba } from 'polished';

export const StyledContainer = styled.div<{ bordered?: boolean }>`
  & .react-mde {
    border: ${({ bordered, theme }) =>
      bordered ? `1px solid` + theme.border.color : 'none'};
    border-radius: ${({ theme }) => theme.component.card.borderRadius};
    overflow: hidden;

    & .mde-textarea-wrapper {
      padding: 6px;
      background-color: ${({ theme }) => theme.palette.background.default};
      border: ${({ bordered }) =>
        bordered ? '1px solid transparent' : 'none'};
      border-radius: 0 0 ${({ theme }) => theme.component.card.borderRadius}
        ${({ theme }) => theme.component.card.borderRadius};

      &:focus-within {
        border-color: ${({ theme }) => theme.palette.primary};
      }

      & textarea {
        padding-inline: ${({ bordered }) => (bordered ? '10px' : 0)};
      }
    }

    & .mde-preview-content {
      padding: ${({ bordered }) => (bordered ? '10px' : '16px 6px')};
    }

    & .mde-text {
      resize: none;
      background-color: transparent;

      &:focus {
        outline: none;
      }
    }

    & .mde-header {
      border-bottom-color: ${({ theme, bordered }) =>
        bordered ? rgba(theme.palette.primary, 0.16) : 'transparent'};
      border-radius: ${({ bordered }) => (bordered ? '12px 12px 0 0' : '12px')};
      // background-color: ${({ theme }) => rgba(theme.palette.primary, 0.16)};
    }

    & .mde-tabs {
      & button {
        border-radius: 10px;
        padding: 2px 8px;
        margin-block: 8px;

        &.selected {
          border-color: ${({ theme }) => theme.palette.primary};
          color: ${({ theme }) => theme.palette.primary};
        }
      }
    }
  }

  & .mde-preview {
    background-color: ${({ theme }) => theme.palette.background.default};
  }
`;
