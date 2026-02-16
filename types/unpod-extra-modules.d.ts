declare module '@unpod/localization/languageData' {
  type LanguageItem = {
    locale: string;
    name: string;
    icon: string;
  };

  const languageData: LanguageItem[];
  export default languageData;
}

declare module 'react-syntax-highlighter/dist/cjs/styles/prism' {
  export const base16AteliersulphurpoolLight: Record<string, unknown>;
}

declare module 'velocity-react' {
  import type { ComponentType, ReactNode } from 'react';

  export type VelocityComponentProps = {
    children?: ReactNode;
    [key: string]: unknown;
  };

  export const VelocityComponent: ComponentType<VelocityComponentProps>;
}

declare module 'monaco-editor' {
  export namespace editor {
    interface IStandaloneCodeEditor {
      getValue(): string;
    }
  }
}

