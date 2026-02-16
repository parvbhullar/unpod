export const AppSetting = {
  CHANGE_LOCALE: 'CHANGE_LOCALE',
  UPDATE_THEME_MODE: 'UPDATE_THEME_MODE',
} as const;

export type AppSettingType = (typeof AppSetting)[keyof typeof AppSetting];

export interface LocaleConfig {
  languageId: string;
  locale: string;
  name: string;
  icon: string;
}

export interface AppContextState {
  locale: LocaleConfig;
  themeMode: 'light' | 'dark' | 'system';
}

export interface AppContextAction {
  type: AppSettingType;
  payload: LocaleConfig | 'light' | 'dark' | 'system';
}

export function contextReducer(state: AppContextState, action: AppContextAction): AppContextState {
  switch (action.type) {
    case AppSetting.CHANGE_LOCALE: {
      return {
        ...state,
        locale: action.payload as LocaleConfig,
      };
    }
    case AppSetting.UPDATE_THEME_MODE: {
      return {
        ...state,
        themeMode: action.payload as 'light' | 'dark' | 'system',
      };
    }

    default:
      return state;
  }
}
