import React from 'react';
import PropTypes from 'prop-types';
import AppMiniWindow from '../../common/AppMiniWindow';
import AddForm from './AddForm';
import {useIntl} from 'react-intl';

const AppNewKb = ({onCreated, addNew, setAddNew}) => {
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
      title={formatMessage({id: 'knowledgeBase.createKnowledgeBase'})}
      onClose={onCloseClick}
    >
      {addNew && <AddForm onSaved={onSaved}/>}
    </AppMiniWindow>
  );
};

AppNewKb.propTypes = {
  addNew: PropTypes.bool,
  setAddNew: PropTypes.func,
  onCreated: PropTypes.func,
};

export default React.memo(AppNewKb);
