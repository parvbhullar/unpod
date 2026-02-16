
import React, { ReactNode } from 'react';
import clsx from 'clsx';
import { StyledCard } from './index.styled';
import { CardProps } from 'antd/es/card';

type AppCardProps = CardProps & {
  children: ReactNode;
  heightFull?: boolean;};

const AppCard: React.FC<AppCardProps> = ({
  title,
  extra,
  children,
  cover,
  className,
  actions,
  heightFull,
  ...rest
}) => {
  return (
    <StyledCard
      className={clsx({ heightFull: heightFull }, className)}
      title={title}
      extra={extra ? extra : null}
      cover={cover}
      actions={actions}
      variant="borderless"
      {...rest}
    >
      {children}
    </StyledCard>
  );
};

export default AppCard;
