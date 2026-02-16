import { HTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';
import { Tooltip, Typography } from 'antd';
import { MdOutlinePhone } from 'react-icons/md';
import { RiLinkUnlink } from 'react-icons/ri';
import { AppPopconfirm } from '@unpod/components/antd';
import {
  StyledActions,
  StyledButton,
  StyledContainer,
  StyledIconWrapper,
  StyledInfoContainer,
  StyledRoot,
  StyledTag,
} from './index.styled';
import { useIntl } from 'react-intl';

const { Text, Paragraph } = Typography;

type NumberCardProps = HTMLAttributes<HTMLDivElement> & {
  item: any;
  providerName?: string;
  onClick?: () => void;
  selected?: boolean;
  hideAvailable?: boolean;
  btnLabel?: string;
  selectedBtnLabel?: string;
  ProviderProfile?: ReactNode;
  onDeleteClick?: (item: any) => void;
};

const NumberCard = ({
  item,
  providerName,
  onClick,
  selected = false,
  hideAvailable = false,
  btnLabel = 'Select',
  selectedBtnLabel = 'Unselect',
  ProviderProfile,
  onDeleteClick,
  ...rest
}: NumberCardProps) => {
  const { formatMessage } = useIntl();

  return (
    <StyledRoot className={clsx({ selected: selected })} {...rest}>
      <StyledContainer>
        <StyledIconWrapper>
          <MdOutlinePhone fontSize={24} />
        </StyledIconWrapper>
        <StyledInfoContainer>
          <Text>{item.number}</Text>
          {providerName && (
            <Paragraph type="secondary">{providerName}</Paragraph>
          )}
        </StyledInfoContainer>
      </StyledContainer>

      {ProviderProfile || (
        <StyledActions>
          {!hideAvailable && (
            <StyledTag color="green">
              {item.active
                ? formatMessage({ id: 'common.available' })
                : formatMessage({ id: 'common.unavailable' })}
            </StyledTag>
          )}

          {onDeleteClick && (
            <AppPopconfirm
              title={formatMessage({ id: 'common.unassign' })}
              description={formatMessage({ id: 'bridges.unassignTitle' })}
              okText={formatMessage({ id: 'common.unassign' })}
              okButtonProps={{ shape: 'round' }}
              onConfirm={() => onDeleteClick(item)}
            >
              <Tooltip title={formatMessage({ id: 'common.unassign' })}>
                <StyledButton
                  type="primary"
                  shape="circle"
                  size="small"
                  icon={<RiLinkUnlink fontSize={18} />}
                  ghost
                />
              </Tooltip>
            </AppPopconfirm>
          )}

          {selected ? (
            <StyledButton shape="round" size="small" onClick={onClick} danger>
              {selectedBtnLabel}
            </StyledButton>
          ) : (
            <StyledButton
              type="primary"
              shape="round"
              size="small"
              onClick={onClick}
              ghost
            >
              {btnLabel}
            </StyledButton>
          )}
        </StyledActions>
      )}
    </StyledRoot>
  );
};

export default NumberCard;
