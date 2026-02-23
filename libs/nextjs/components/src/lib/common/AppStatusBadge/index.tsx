import {type HTMLAttributes, memo, type ReactNode} from 'react';
import styled, {css, keyframes} from 'styled-components';

const opacityWave = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
`;

type BadgeSize = 'small' | 'medium' | 'large';
type BadgeShape = 'round' | 'square';

const StyleBadge = styled.span<{
  $shape?: BadgeShape;
  $size?: BadgeSize;
  $animateWave?: boolean;
}>`
  font-size: ${({theme}) => theme.font.size.sm};
  text-transform: capitalize;
  border-radius: ${({$shape, $size}) => {
  if ($shape === 'round') return '20px';
  return $size === 'medium' ? '20px' : '6px';
}};
  // max-width: ${({$size}) => ($size === 'medium' ? '120px' : '100px')};
  // min-width: ${({$size}) => ($size === 'medium' ? '80px' : '60px')};
  text-align: center;
  padding: ${({$shape, $size}) => {
  if ($shape === 'round') return '1px 14px';
  return $size === 'medium' ? '5px 8px' : '2px 6px';
}};

  font-weight: ${({$size}) => ($size === 'medium' ? 500 : 400)};
  // color: ${({theme}) => theme.palette.text.primary};
  cursor: pointer;
  white-space: nowrap;

  ${({$animateWave}) =>
  $animateWave &&
  css`
      animation: ${opacityWave} 2s infinite;
    `}
`;

type StatusColors = {
  [key: string]: { color: string; label: ReactNode };
};

type AppStatusBadgeProps = HTMLAttributes<HTMLSpanElement> & {
  status?: string;
  name?: string;
  size?: BadgeSize;
  statusColors?: StatusColors;
  shape?: BadgeShape;
  animate?: boolean;
};

export const AppStatusBadge = ({
                                 status,
                                 name,
                                 size = 'medium',
                                 statusColors,
                                 shape,
                                 animate = false,
                                 ...restProps
                               }: AppStatusBadgeProps) => {
  const statusObj = status && statusColors ? statusColors[status] : null;

  return statusObj ? (
    <StyleBadge
      className={`badge ${statusObj.color}`}
      $size={size}
      $shape={shape}
      $animateWave={animate}
      {...restProps}
    >
      {statusObj.label}
    </StyleBadge>
  ) : name ? (
    <StyleBadge
      className="badge badge-warning"
      $size={size}
      $shape={shape}
      $animateWave={animate}
      {...restProps}
    >
      {name}
    </StyleBadge>
  ) : null;
};

export default memo(AppStatusBadge);
