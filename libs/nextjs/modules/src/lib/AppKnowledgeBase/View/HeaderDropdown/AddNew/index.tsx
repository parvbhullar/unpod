import React from 'react';
import AppMiniWindow from '@unpod/components/common/AppMiniWindow';
import AddForm from './AddForm';
import { useIntl } from 'react-intl';

const AddNew = ({ onCreated, addNew, setAddNew }) => {
  const {formatMessage} = useIntl();
  const onSaved = (response) => {
    localStorage.removeItem(`save-kb`);
    onCloseClick();
    if (onCreated) onCreated(response);
  };

  const onCloseClick = () => {
    setAddNew(false);
  };

  return (
    <AppMiniWindow
      open={addNew}
      title={formatMessage({ id: 'knowledgeBase.create' })}
      onClose={onCloseClick}
    >
      {addNew && <AddForm onSaved={onSaved} />}
    </AppMiniWindow>
  );
};

AddNew.propTypes = {
  addNew: PropTypes.bool,
  setAddNew: PropTypes.func,
  onCreated: PropTypes.func,
};

export default React.memo(AddNew);
