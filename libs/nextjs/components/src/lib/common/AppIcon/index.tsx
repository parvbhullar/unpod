import React, { CSSProperties, MouseEventHandler, ReactNode } from 'react';
import { theme, Tooltip } from 'antd';
import { TooltipPlacement } from 'antd/es/tooltip';

import {
  AppBusinessIcon,
  AppDeleteIcon,
  AppDownloadIcon,
  AppEditIcon,
  AppInvestorIcon,
  AppMentorIcon,
  AppUserIcon,
  AppViewIcon,
} from '@unpod/icons';

import { StyledButton, StyledIconButton, StyledSpace } from './index.styled';
import { getAssetsUrl } from '@unpod/helpers/UrlHelper';

type AppIconType =
  | 'user'
  | 'saas'
  | 'business'
  | 'building'
  | 'company'
  | 'd2c'
  | 'mentor'
  | 'talent'
  | 'mentorship'
  | 'influencer'
  | 'graduation-hat'
  | 'investor'
  | 'briefcase'
  | 'marketplace'
  | 'feedback'
  | 'funding'
  | 'edit'
  | 'delete'
  | 'view'
  | 'download'
  | (string & {});

const getIcon = (icon: AppIconType): ReactNode => {
  switch (icon) {
    case 'user':
    case 'saas':
      return <AppUserIcon />;
    case 'business':
    case 'building':
    case 'company':
    case 'd2c':
      return <AppBusinessIcon />;
    case 'mentor':
    case 'talent':
    case 'mentorship':
    case 'influencer':
    case 'graduation-hat':
      return <AppMentorIcon />;
    case 'investor':
    case 'briefcase':
    case 'marketplace':
    case 'feedback':
    case 'funding':
      return <AppInvestorIcon />;
    case 'edit':
      return <AppEditIcon />;
    case 'delete':
      return <AppDeleteIcon />;
    case 'view':
      return <AppViewIcon />;
    case 'download':
      return <AppDownloadIcon />;
    default:
      return (
        <span className={`pointer anticon anticon-${icon}`}>
          <img src={getAssetsUrl(`icons/${icon}.svg`)} alt={icon as string} />
        </span>
      );
  }
};

const { useToken } = theme;

type AppIconProps = {
  title?: string;
  onClick?: MouseEventHandler<HTMLElement>;
  icon: AppIconType;
  placement?: TooltipPlacement;
  style?: CSSProperties;
  showToolTip?: boolean;
  btnWrapper?: boolean;
  disabled?: boolean;
  [key: string]: unknown;};

export const AppIcon: React.FC<AppIconProps> = ({
  title,
  onClick,
  icon,
  placement,
  style,
  showToolTip = true,
  btnWrapper,
  disabled = false,
  ...rest
}) => {
  const { token } = useToken();
  if (showToolTip)
    return (
      <Tooltip title={title} placement={placement} mi-role={'title'}>
        {btnWrapper ? (
          <StyledIconButton
            onClick={onClick}
            style={{
              color: icon === 'delete' ? token.colorError : token.colorPrimary,
              background: 'transparent',
              cursor: disabled ? 'not-allowed' : 'pointer',
              ...style,
            }}
            icon={getIcon(icon)}
            {...rest}
          />
        ) : (
          <span
            onClick={onClick}
            style={{
              color: icon === 'delete' ? token.colorError : token.colorPrimary,
              cursor: disabled ? 'not-allowed' : 'pointer',
              ...style,
            }}
            {...rest}
          >
            {getIcon(icon)}
          </span>
        )}
      </Tooltip>
    );

  return btnWrapper ? (
    <StyledButton
      onClick={onClick}
      style={{
        color: icon === 'delete' ? token.colorError : token.colorPrimary,
        cursor: disabled ? 'not-allowed' : 'pointer',
        ...style,
      }}
      icon={getIcon(icon)}
      {...rest}
    >
      {title}
    </StyledButton>
  ) : (
    <StyledSpace
      onClick={onClick}
      style={{
        color: icon === 'delete' ? token.colorError : token.colorPrimary,
        cursor: disabled ? 'not-allowed' : 'pointer',

        ...style,
      }}
    >
      {getIcon(icon)}
      <span>{title}</span>
    </StyledSpace>
  );
};

export default AppIcon;
