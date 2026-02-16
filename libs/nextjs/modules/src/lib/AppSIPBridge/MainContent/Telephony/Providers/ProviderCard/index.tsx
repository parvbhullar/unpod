import { ReactNode } from 'react';
import { Button, Typography } from 'antd';
import AppImage from '@unpod/components/next/AppImage';

import clsx from 'clsx';
import {
  StyledActionWrapper,
  StyledIconWrapper,
  StyledMainContent,
  StyledMainInfo,
  StyledRoot,
} from './index.styled';
import AppWarningTooltip from '@unpod/components/common/AppWarningLabel';

const { Text } = Typography;

type ProviderCardProps = {
  provider: any;
  btnLabel?: string;
  selected?: boolean;
  onButtonClick?: (provider: any) => void;
  hideAction?: boolean;
  valid?: boolean | null;
  extra?: ReactNode;
};

const ProviderCard = ({
  provider,
  btnLabel = 'Configure',
  selected,
  onButtonClick,
  hideAction = false,
  valid = null,
  extra,
}: ProviderCardProps) => {
  return (
    <StyledRoot className={clsx({ selected: selected })}>
      <StyledMainContent>
        <StyledIconWrapper>
          <AppImage
            src={provider.icon}
            alt={provider.name}
            width={30}
            height={30}
          />
        </StyledIconWrapper>
        <StyledMainInfo>
          <Text
            style={{
              textTransform: 'Capitalize',
              fontWeight: 700,
            }}
          >
            {provider.name}
          </Text>
        </StyledMainInfo>
      </StyledMainContent>

      {!hideAction && (
        <StyledActionWrapper $extra={Boolean(extra)}>
          {!valid && <AppWarningTooltip />}
          {!selected && (
            <Button
              type="primary"
              shape="round"
              size="small"
              onClick={() => onButtonClick?.(provider)}
              danger={selected}
              ghost
            >
              {btnLabel}
            </Button>
          )}

          {extra}
        </StyledActionWrapper>
      )}
    </StyledRoot>
  );
};

export default ProviderCard;
