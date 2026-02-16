import React from 'react';
import { useAutoplayError } from '@100mslive/react-sdk';
import { Button, Modal } from 'antd';

export function AutoplayBlockedModal() {
  const { error, resetError, unblockAudio } = useAutoplayError();
  return (
    <Modal
      open={!!error}
      onCancel={(value) => {
        if (!value) {
          unblockAudio();
        }
        resetError();
      }}
      footer={
        <Button
          type="primary"
          onClick={() => {
            unblockAudio();
            resetError();
          }}
        >
          Allow Audio
        </Button>
      }
    ></Modal>
  );
}
