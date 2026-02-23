'use client';

import {Dropdown, Space} from 'antd';
import {DownOutlined, GlobalOutlined} from '@ant-design/icons';
import {useAppActionsContext, useAppContext} from '@unpod/providers';
import languageData from '@unpod/localization/languageData';
import {StyledCurrentLanguage, StyledLanguageItem, StyledLanguageSwitcher,} from './index.styled';

type LanguageItem = {
  languageId?: string;
  locale: string;
  name: string;
  icon: string;
};

type AppLanguageSwitcherProps = {
  showLabel?: boolean;
  showIcon?: boolean;
};

const AppLanguageSwitcher: React.FC<AppLanguageSwitcherProps> = ({
                                                                   showLabel = true,
                                                                   showIcon = true,
                                                                 }) => {
  const {locale} = useAppContext();
  const {updateLocale} = useAppActionsContext();

  const handleLanguageChange = (language: LanguageItem) => {
    updateLocale({
      ...language,
      languageId: language.languageId ?? language.locale,
    });
  };

  const menuItems = (languageData as LanguageItem[]).map((lang) => ({
    key: lang.locale,
    label: (
      <StyledLanguageItem
        onClick={() => handleLanguageChange(lang)}
        $isActive={locale.locale === lang.locale}
      >
        <span className="flag-icon">{getFlagEmoji(lang.icon)}</span>
        <span className="language-name">{lang.name}</span>
      </StyledLanguageItem>
    ),
  }));

  return (
    <StyledLanguageSwitcher>
      <Dropdown
        menu={{items: menuItems}}
        trigger={['click']}
        placement="bottomRight"
      >
        <StyledCurrentLanguage>
          <Space>
            {showIcon && <GlobalOutlined/>}
            {showLabel && (
              <>
                <span className="flag-icon">{getFlagEmoji(locale.icon)}</span>
                <span className="language-name">{locale.name}</span>
              </>
            )}
            <DownOutlined style={{fontSize: 10}}/>
          </Space>
        </StyledCurrentLanguage>
      </Dropdown>
    </StyledLanguageSwitcher>
  );
};

const getFlagEmoji = (countryCode: string) => {
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map((char: string) => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
};

export default AppLanguageSwitcher;
