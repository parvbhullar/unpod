import styled from 'styled-components';

export const StyledLanguageSwitcher = styled.div`
  display: inline-flex;
  align-items: center;
`;

export const StyledCurrentLanguage = styled.div`
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: rgba(0, 0, 0, 0.04);
  }

  .flag-icon {
    font-size: 16px;
    line-height: 1;
  }

  .language-name {
    font-size: 14px;
    margin-left: 4px;
  }

  [dir='rtl'] & {
    .language-name {
      margin-left: 0;
      margin-right: 4px;
    }
  }
`;

type StyledLanguageItemProps = {
  $isActive?: boolean;
};

export const StyledLanguageItem = styled.div<StyledLanguageItemProps>`
  display: flex;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  min-width: 140px;
  background-color: ${(props) =>
  props.$isActive ? 'rgba(0, 0, 0, 0.04)' : 'transparent'};
  font-weight: ${(props) => (props.$isActive ? 600 : 400)};

  .flag-icon {
    font-size: 18px;
    line-height: 1;
    margin-right: 12px;
  }

  .language-name {
    font-size: 14px;
  }

  &:hover {
    background-color: rgba(0, 0, 0, 0.06);
  }

  [dir='rtl'] & {
    .flag-icon {
      margin-right: 0;
      margin-left: 12px;
    }
  }
`;
