import { useState } from 'react';
import { Button, Dropdown } from 'antd';
import { MdDelete, MdEdit, MdMoreVert } from 'react-icons/md';
import { deleteDataApi, useInfoViewActionsContext } from '@unpod/providers';
import ProviderCard from '../ProviderCard';
import ConfigureForm from '../ConfigureForm';
import AppList from '@unpod/components/common/AppList';
import { useApp } from '@unpod/custom-hooks';
import { useIntl } from 'react-intl';

const items = [
  {
    key: 'edit',
    label: 'common.edit',
    icon: (
      <span className="ant-icon">
        <MdEdit fontSize={16} />
      </span>
    ),
  },
  {
    key: 'delete',
    label: 'common.delete',
    icon: (
      <span className="ant-icon">
        <MdDelete fontSize={16} />
      </span>
    ),
  },
];

const Configured = ({
  providers = [],
  setConfigured,
  onLinkNumber,
  selectedNumber,
}: {
  providers?: any[];
  setConfigured: (data: any[]) => void;
  onLinkNumber: (provider: any, selected: boolean) => void;
  selectedNumber: any;
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();

  const [selectedProvider, setSelectedProvider] = useState<any | null>(null);
  const [isEditOpen, setEditOpen] = useState(false);
  const { openConfirmModal } = useApp();

  const onMenuClick = (key: string, item: any) => {
    if (key === 'edit') {
      setSelectedProvider(item);
      setEditOpen(true);
    } else if (key === 'delete') {
      confirmDelete(item);
    }
  };

  const onConfigured = (data: any) => {
    setConfigured(
      providers.map((item: any) => {
        if (item.id === data.id) {
          return {
            ...item,
            ...data,
          };
        }
        return item;
      }),
    );

    setSelectedProvider(null);
    setEditOpen(false);
  };

  const confirmDelete = (provider: any) => {
    openConfirmModal({
      content: formatMessage({ id: 'modal.confirmDeleteContent' }),
      onOk: () => onDelete(provider),
    });
  };

  const onDelete = (provider: any) => {
    deleteDataApi(
      `telephony/provider-credentials/${provider.credentials.id}/`,
      infoViewActionsContext,
    )
      .then(() => {
        infoViewActionsContext.showMessage('Deleted successfully');
        setConfigured(
          providers.filter((item: any) => item.id !== provider.credentials.id),
        );
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onCancel = () => {
    setEditOpen(false);
    setSelectedProvider(null);
  };

  const selectedProviderAny = selectedProvider as any;

  return isEditOpen && selectedProviderAny ? (
    <ConfigureForm
      provider={selectedProviderAny}
      credentials={selectedProviderAny.credentials}
      onCancel={onCancel}
      onConfigured={onConfigured}
    />
  ) : (
    <AppList
      data={providers}
      noDataMessage={formatMessage({ id: 'bridge.configureNoDataMessage' })}
      renderItem={(provider: any, index: number) => {
        const { provider_details, ...rest } = provider || {};
        const item = {
          ...provider_details,
          credentials: rest,
        };

        const selected = rest.id === selectedNumber?.provider_credential?.id;
        const providerMenuOptions = selected
          ? items.filter((item) => item.key !== 'delete')
          : items;

        return (
          <ProviderCard
            key={index}
            provider={{
              ...item,
              name: `${rest.name} (${provider_details?.name})`,
            }}
            btnLabel={
              selected
                ? formatMessage({ id: 'common.unselect' })
                : formatMessage({ id: 'common.select' })
            }
            onButtonClick={() => onLinkNumber(item, selected)}
            selected={selected}
            valid={rest?.is_valid}
            extra={
              <Dropdown
                menu={{
                  items: providerMenuOptions.map((item) => ({
                    ...item,
                    label: formatMessage({ id: item.label }),
                  })),
                  onClick: ({ key }) => onMenuClick(key, item),
                }}
                trigger={['click']}
                placement="bottomRight"
              >
                <Button
                  shape="circle"
                  size="small"
                  icon={<MdMoreVert fontSize={16} />}
                />
              </Dropdown>
            }
          />
        );
      }}
    />
  );
};

export default Configured;
