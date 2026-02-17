import Overview from './MainContent/Overview';
import Telephony from './MainContent/Telephony';
import Documents from './MainContent/Documents';
import { ReactNode } from 'react';

export const TAB_KEYS = ['telephony', 'documents', 'overview'];

type FormatMessage = (descriptor: { id: string }) => string;

type GetTabItemsProps = {
  formatMessage: FormatMessage;
  isNewRecord?: boolean;
  [key: string]: any;
};

export const getTabItems = (props: GetTabItemsProps) => {
  const items: Array<{
    key: string;
    label: any;
    disabled?: boolean;
    children: ReactNode;
  }> = [
    {
      key: 'telephony',
      label: props.formatMessage({ id: 'tab.telephony' }),
      disabled: props.isNewRecord,
      children: <Telephony {...(props as any)} />,
    },
    {
      key: 'documents',
      label: props.formatMessage({ id: 'tab.documents' }),
      disabled: props.isNewRecord,
      children: <Documents {...(props as any)} />,
    },
  ];
  if (props.isNewRecord) {
    items.unshift({
      key: 'overview',
      label: props.formatMessage({ id: 'tab.overview' }),
      disabled: false,
      children: <Overview {...(props as any)} />,
    });
  }

  return items;
};
