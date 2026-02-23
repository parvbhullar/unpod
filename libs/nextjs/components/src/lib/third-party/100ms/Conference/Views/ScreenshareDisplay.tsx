import React from 'react';
import {useHMSActions} from '@100mslive/react-sdk';
import {Button} from 'antd';
import {AiOutlineCloseCircle} from 'react-icons/ai';
import {MdOutlineScreenShare} from 'react-icons/md';

export const ScreenshareDisplay = () => {
  const hmsActions = useHMSActions();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden',
        width: '37.5rem',
        maxWidth: '80%',
        height: '100%',
        borderRadius: '$3',
        margin: '0 auto',
        textAlign: 'center',
      }}
    >
      <MdOutlineScreenShare/>
      <h5 style={{margin: '32px 0'}}>You are sharing your screen</h5>
      <Button
        variant="danger"
        onClick={async () => {
          await hmsActions.setScreenShareEnabled(false);
        }}
        icon={<AiOutlineCloseCircle/>}
        data-testid="stop_screen_share_btn"
      >
        Stop screen share
      </Button>
    </div>
  );
};
