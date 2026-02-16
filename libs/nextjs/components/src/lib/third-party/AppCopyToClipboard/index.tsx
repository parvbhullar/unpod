
import { CopyToClipboard } from '@unpod/external-libs/react-copy-to-clipboard';
import { useInfoViewActionsContext } from '@unpod/providers';

import styled from 'styled-components';
import { Button, Tooltip } from 'antd';
import { MdOutlineContentCopy } from 'react-icons/md';

type StyledTextProps = {
  $textColor?: string;
};

export const StyledText = styled.span<StyledTextProps>`
  color: ${({ theme, $textColor }) =>
    $textColor === 'black'
      ? 'rgba(58, 58, 58, 0.88)'
      : $textColor === 'white'
        ? theme.palette.common.white
        : theme.palette.primary};
  cursor: pointer;
`;

type IconProps = {
  iconFontSize?: number;};

const Icon: React.FC<IconProps> = ({ iconFontSize }) => (
  <Button
    type="text"
    size="small"
    shape="circle"
    icon={<MdOutlineContentCopy fontSize={iconFontSize} />}
  />
);

type AppCopyToClipboardProps = {
  title?: string;
  showToolTip?: boolean;
  iconFontSize?: number;
  text?: string;
  onCopy?: () => void;
  textColor?: 'black' | 'white' | string;
  hideIcon?: boolean;};

const AppCopyToClipboard: React.FC<AppCopyToClipboardProps> = ({
  title = 'Copy Link',
  showToolTip,
  iconFontSize = 16,
  text = '',
  onCopy,
  textColor,
  hideIcon = true,
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  return (
    <CopyToClipboard
      text={text}
      onCopy={() => {
        if (onCopy) {
          onCopy();
        }
        infoViewActionsContext.showMessage('Copied');
      }}
    >
      <span>
        {hideIcon &&
          (showToolTip ? (
            <Tooltip title="Copy">
              <Icon iconFontSize={iconFontSize} />
            </Tooltip>
          ) : (
            <Icon iconFontSize={iconFontSize} />
          ))}

        {title && <StyledText $textColor={textColor}>{title}</StyledText>}
      </span>
    </CopyToClipboard>
  );
};

export default AppCopyToClipboard;
