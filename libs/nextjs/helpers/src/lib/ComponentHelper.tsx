'use client';

import { Modal, ModalFuncProps } from 'antd';
import { FormatMessageFn } from './LocalizationFormatHelper';

export const openConfirmModal = (
  props: ModalFuncProps,
  formatMessage: FormatMessageFn,
): void => {
  Modal.confirm({
    title: formatMessage({ id: 'knowledgeBase.confirmDeleteTitle' }),
    icon: null,
    content: formatMessage({ id: 'knowledgeBase.confirmDeleteContent' }),
    cancelText: formatMessage({ id: 'common.cancel' }),
    cancelButtonProps: {
      shape: 'round',
    },
    okText: formatMessage({ id: 'common.delete' }),
    okButtonProps: {
      danger: true,
      shape: 'round',
    },
    ...props,
  });
};
