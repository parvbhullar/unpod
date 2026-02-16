import React from 'react';
import {
  selectRoleChangeRequest,
  useHMSActions,
  useHMSStore,
} from '@100mslive/react-sdk';
import AppConfirmModal from '../../../antd/AppConfirmModal';

export const RoleChangeRequestModal = () => {
  const hmsActions = useHMSActions();
  const roleChangeRequest = useHMSStore(selectRoleChangeRequest);

  if (!roleChangeRequest?.role) {
    return null;
  }

  return (
    <AppConfirmModal
      title="Role Change Request"
      onCancel={(value) =>
        !value && hmsActions.rejectChangeRole(roleChangeRequest)
      }
      onOk={() => {
        hmsActions.acceptChangeRole(roleChangeRequest);
      }}
      cancelText={'Cancel'}
      okText={'Accept'}
      isDanger={false}
      message={`${roleChangeRequest?.requestedBy?.name} has requested you to change your role to ${roleChangeRequest?.role?.name}.`}
    />
  );
};
