import AddForm from './AddForm';
import AppDrawer from '../../antd/AppDrawer';
import {useIntl} from 'react-intl';
import {useMediaQuery} from 'react-responsive';
import {MobileWidthQuery} from '@unpod/constants';

type AppCreateKbProps = {
  onCreated?: (response: any) => void;
  addNew?: boolean;
  setAddNew: (open: boolean) => void;
};

const AppCreateKb = ({onCreated, addNew, setAddNew}: AppCreateKbProps) => {
  const {formatMessage} = useIntl();
  const isMobile = useMediaQuery(MobileWidthQuery);

  const onSaved = (response: any) => {
    localStorage.removeItem(`save-kb`);
    onCloseClick();
    if (onCreated) onCreated(response);
  };

  const onCloseClick = () => {
    setAddNew(false);
  };

  return (
    <AppDrawer
      open={addNew}
      title={formatMessage({id: 'knowledgeBase.createKnowledgeBase'})}
      size={isMobile ? '100%' : 'calc(100% - 405px)'}
    >
      <AddForm onSaved={onSaved} onClose={onCloseClick}/>
    </AppDrawer>
  );
};

export default AppCreateKb;
