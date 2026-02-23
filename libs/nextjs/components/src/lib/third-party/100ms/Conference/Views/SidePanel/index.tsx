import React from 'react';
import {selectAppData, useHMSStore} from '@100mslive/react-sdk';
import {ParticipantList} from './ParticipantList';
import {APP_DATA, SIDE_PANE_OPTIONS} from '../../../common/constants';

const SidePanel = ({css = {}}) => {
  const sidepane = useHMSStore(selectAppData(APP_DATA.sidePane));
  let ViewComponent;
  if (sidepane === SIDE_PANE_OPTIONS.PARTICIPANTS) {
    ViewComponent = ParticipantList;
  }
  if (!ViewComponent) {
    return null;
  }
  return (
    <div
      style={{
        position: 'absolute',
        width: 400,
        height: '100%',
        padding: 40,
        backgroundColor: '#afafaf',
        borderRadius: 4,
        top: 0,
        right: 20,
        zIndex: 10,
        boxShadow: '0 0 8px 0 rgba(0,0,0,0.3)',
      }}
    >
      <ViewComponent/>
    </div>
  );
};

export default SidePanel;
