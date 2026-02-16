import { Tooltip } from 'antd';
import { IoWarning } from 'react-icons/io5';
import { useIntl } from 'react-intl';
import type { CSSProperties } from 'react';

type AppWarningTooltipProps = {
  message?: string;
  style?: CSSProperties;};

const AppWarningTooltip = ({
  message = 'bridge.providerWarning',
  style,
}: AppWarningTooltipProps) => {
  const { formatMessage } = useIntl();
  return (
    <Tooltip title={formatMessage({ id: message })}>
      <IoWarning
        style={{
          color: '#ffaa00ff',
          fontSize: 18,
          alignSelf: 'center',
          ...style,
        }}
      />
    </Tooltip>
  );
};

export default AppWarningTooltip;
