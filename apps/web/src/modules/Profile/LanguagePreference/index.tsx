'use client';
import React, { useEffect } from 'react';
import { Button, Form, Row, Select } from 'antd';
import { StyledRoot } from './index.styled';
import {
  putDataApi,
  useAuthActionsContext,
  useInfoViewActionsContext,
  useLocale,
} from '@unpod/providers';
import { useIntl } from 'react-intl';
import type { User } from '@unpod/constants/types';

const { Item } = Form;

const AVAILABLE_LANGUAGES = [
  { code: 'en', name: 'English', languageId: 'english', icon: 'us' },
  { code: 'hi', name: 'हिन्दी (Hindi)', languageId: 'hindi', icon: 'in' },
  { code: 'ar', name: 'العربية (Arabic)', languageId: 'arabic', icon: 'sa' },
  { code: 'bn', name: 'বাংলা (Bengali)', languageId: 'bengali', icon: 'bd' },
  { code: 'zh', name: '中文 (Chinese)', languageId: 'chinese', icon: 'cn' },
  { code: 'de', name: 'Deutsch (German)', languageId: 'german', icon: 'de' },
  { code: 'es', name: 'Español (Spanish)', languageId: 'spanish', icon: 'es' },
  { code: 'fr', name: 'Français (French)', languageId: 'french', icon: 'fr' },
  {
    code: 'gu',
    name: 'ગુજરાતી (Gujarati)',
    languageId: 'gujarati',
    icon: 'in',
  },
  { code: 'it', name: 'Italiano (Italian)', languageId: 'italian', icon: 'it' },
  { code: 'ja', name: '日本語 (Japanese)', languageId: 'japanese', icon: 'jp' },
  { code: 'ko', name: '한국어 (Korean)', languageId: 'korean', icon: 'kr' },
  { code: 'mr', name: 'मराठी (Marathi)', languageId: 'marathi', icon: 'in' },
  { code: 'nl', name: 'Nederlands (Dutch)', languageId: 'dutch', icon: 'nl' },
  { code: 'pa', name: 'ਪੰਜਾਬੀ (Punjabi)', languageId: 'punjabi', icon: 'in' },
  { code: 'pl', name: 'Polski (Polish)', languageId: 'polish', icon: 'pl' },
  {
    code: 'pt',
    name: 'Português (Portuguese)',
    languageId: 'portuguese',
    icon: 'pt',
  },
  { code: 'ru', name: 'Русский (Russian)', languageId: 'russian', icon: 'ru' },
  { code: 'ta', name: 'தமிழ் (Tamil)', languageId: 'tamil', icon: 'in' },
  { code: 'te', name: 'తెలుగు (Telugu)', languageId: 'telugu', icon: 'in' },
];

type LanguagePreferenceProps = {
  user: User;
};

type FormValues = {
  preferred_language: string;
};

const LanguagePreference: React.FC<LanguagePreferenceProps> = ({ user }) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { updateAuthUser } = useAuthActionsContext();
  const { formatMessage } = useIntl();
  const { locale, changeLocale } = useLocale();
  const [form] = Form.useForm();

  useEffect(() => {
    // Check localStorage first, then user preference, then context locale
    const storedLanguage = localStorage.getItem('preferred_language');
    const preferred =
      typeof user?.user_detail?.preferred_language === 'string'
        ? user.user_detail.preferred_language
        : '';
    const userLocale = storedLanguage || preferred || locale;

    form.setFieldsValue({
      preferred_language: userLocale,
    });

    // Store in localStorage if not already stored
    if (!storedLanguage && userLocale) {
      localStorage.setItem('preferred_language', String(userLocale));
    }
  }, [user, locale, form]);

  const onSubmitSuccess = (formData: FormValues) => {
    const selectedLangCode = formData.preferred_language;
    const selectedLangObj = AVAILABLE_LANGUAGES.find(
      (lang) => lang.code === selectedLangCode,
    );

    // Update backend
    putDataApi('user-profile/', infoViewActionsContext, {
      preferred_language: selectedLangCode,
    })
      .then((response) => {
        const res = response as { message?: string };
        // Store in localStorage
        localStorage.setItem('preferred_language', selectedLangCode);

        infoViewActionsContext.showMessage(
          formatMessage({ id: 'profile.languageUpdated' }) ||
            res.message ||
            'Language preference updated successfully',
        );

        // Update user context
        updateAuthUser({
          ...user,
          user_detail: {
            ...user.user_detail,
            preferred_language: selectedLangCode,
          },
        });

        // Update locale in AppContext
        if (selectedLangObj) {
          changeLocale({
            languageId: selectedLangObj.languageId,
            locale: selectedLangObj.code,
            name: selectedLangObj.name,
            icon: selectedLangObj.icon,
          });
        }
      })
      .catch((response) => {
        const err = response as { message?: string };
        infoViewActionsContext.showError(
          err.message || 'Failed to update language preference',
        );
      });
  };

  return (
    <StyledRoot>
      <Form form={form} onFinish={onSubmitSuccess} layout="vertical">
        <Item
          name="preferred_language"
          label={
            formatMessage({ id: 'profile.selectLanguage' }) || 'Select Language'
          }
          rules={[
            {
              required: true,
              message:
                formatMessage({ id: 'validation.selectLanguage' }) ||
                'Please select a language',
            },
          ]}
        >
          <Select
            placeholder={
              formatMessage({ id: 'profile.selectLanguagePlaceholder' }) ||
              'Choose your preferred language'
            }
            style={{ width: '100%', maxWidth: '400px' }}
            showSearch
            filterOption={(input, option) => {
              const optionData = option as {
                value?: string;
                children?: React.ReactNode;
                languageId?: string;
              };
              const query = (input || '').toString().toLowerCase();
              const value = (optionData?.value || '').toString().toLowerCase();
              const name = (optionData?.children || '')
                .toString()
                .toLowerCase();
              const languageId = (optionData?.languageId || '')
                .toString()
                .toLowerCase();
              return (
                value.includes(query) ||
                name.includes(query) ||
                languageId.includes(query)
              );
            }}
          >
            {AVAILABLE_LANGUAGES.map((lang) => (
              <Select.Option key={lang.code} value={lang.code}>
                {lang.name}
              </Select.Option>
            ))}
          </Select>
        </Item>

        <Row>
          <Button type="primary" htmlType="submit">
            {formatMessage({ id: 'common.saveChanges' }) || 'Save Changes'}
          </Button>
        </Row>
      </Form>
    </StyledRoot>
  );
};

export default LanguagePreference;
