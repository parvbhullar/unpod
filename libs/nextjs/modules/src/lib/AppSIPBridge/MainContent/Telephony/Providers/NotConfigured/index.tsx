import { useState } from 'react';
import { StyledRoot } from './index.styled';
import ProviderCard from '../ProviderCard';
import ConfigureForm from '../ConfigureForm';
import AppList from '@unpod/components/common/AppList';
import { useIntl } from 'react-intl';

const NotConfigured = ({
  loading,
  providers = [],
  onProviderConfigured,
}: {
  loading: boolean;
  providers?: any[];
  onProviderConfigured: (data: any) => void;
}) => {
  const [selectedProvider, setSelectedProvider] = useState<any | null>(null);
  const { formatMessage } = useIntl();

  const onButtonClick = (provider: any) => {
    // This function can be used to handle button clicks for each provider
    console.log(`Button clicked for provider: ${provider.name}`);
    setSelectedProvider(provider);
  };

  const onCancel = () => {
    // This function can be used to handle cancel action in the form
    setSelectedProvider(null);
  };

  const onConfigured = (data: any) => {
    onProviderConfigured(data);
    setSelectedProvider(null);
  };

  return (
    <StyledRoot>
      {selectedProvider ? (
        <ConfigureForm
          provider={selectedProvider}
          onCancel={onCancel}
          onConfigured={onConfigured}
        />
      ) : (
        <AppList
          data={providers}
          loading={loading}
          renderItem={(provider: any, index: number) => (
            <ProviderCard
              key={index}
              provider={provider}
              onButtonClick={onButtonClick}
              btnLabel={formatMessage({ id: 'bridge.configure' })}
              selected={false}
              extra={null}
              valid={true}
            />
          )}
          noDataMessage={formatMessage({ id: 'bridge.noDataMessage' })}
        />
      )}
    </StyledRoot>
  );
};

export default NotConfigured;
