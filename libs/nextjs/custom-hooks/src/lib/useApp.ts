import {App} from 'antd';
import {ModalFuncProps} from 'antd/es/modal/interface';
import {useIntl} from 'react-intl';

export type UseAppResult = {
  openConfirmModal: (props?: ModalFuncProps) => void;
};

export const useApp = (): UseAppResult => {
  const {modal} = App.useApp();
  const {formatMessage} = useIntl();

  const openConfirmModal = (props?: ModalFuncProps): void => {
    modal.confirm({
      title: formatMessage({id: 'modal.confirmDeleteTitle'}),
      icon: null,
      content: formatMessage({id: 'modal.confirmDeleteContent'}),
      cancelText: formatMessage({id: 'common.cancel'}),
      cancelButtonProps: {
        shape: 'round',
      },
      okText: formatMessage({id: 'common.delete'}),
      okButtonProps: {
        danger: true,
        shape: 'round',
      },
      ...props,
    });
  };
  return {
    openConfirmModal,
  };
};
