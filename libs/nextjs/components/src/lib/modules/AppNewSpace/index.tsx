
import AddForm from '../AppCreateKb/AddForm';
import { AppDrawer } from '../../antd';
import { useIntl } from 'react-intl';

type AppNewSpaceProps = {
  content_type?: string;
  onSpaceCreated?: (response: any) => void;
  openForm: boolean;
  setFormOpen: (open: boolean) => void;};

const AppNewSpace = ({
  content_type,
  onSpaceCreated,
  openForm,
  setFormOpen,
}: AppNewSpaceProps) => {
  const { formatMessage } = useIntl();
  const onSpaceSaved = (response: any) => {
    localStorage.removeItem(`save-space`);
    onCloseClick();
    if (onSpaceCreated) onSpaceCreated(response);
  };

  const onCloseClick = () => {
    setFormOpen(false);
  };

  return (
    <AppDrawer
      open={openForm}
      title={formatMessage({ id: 'dashboard.createSpaceTitle' })}
      onClose={onCloseClick}
    >
      {openForm && (
        <AddForm
          isSpace
          onSaved={onSpaceSaved}
          content_type={content_type}
          onClose={onCloseClick}
        />
      )}
    </AppDrawer>
  );
};

export default AppNewSpace;
