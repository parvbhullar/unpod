declare module '@unpod/components/modules/AppQueryWindow' {
  import type { ComponentType } from 'react';

  export type AppQueryWindowProps = {
    pilotPopover?: boolean;
    [key: string]: unknown;
  };

  const AppQueryWindow: ComponentType<AppQueryWindowProps>;
  export default AppQueryWindow;
}

declare module '@unpod/components/third-party/AppEditor/AppEditorInput' {
  import type { ComponentType, KeyboardEvent } from 'react';

  export type AppEditorInputProps = {
    placeholder?: string;
    value?: string;
    onChange?: (content: string) => void;
    onKeyDown?: (event: KeyboardEvent<HTMLElement>) => void;
    [key: string]: unknown;
  };

  const AppEditorInput: ComponentType<AppEditorInputProps>;
  export default AppEditorInput;
}

declare module 'react-anchor-link-smooth-scroll' {
  import type { AnchorHTMLAttributes, ComponentType } from 'react';

  const AnchorLink: ComponentType<AnchorHTMLAttributes<HTMLAnchorElement>>;
  export default AnchorLink;
}

