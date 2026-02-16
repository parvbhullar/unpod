import React, { ComponentProps, ReactNode } from 'react';
import SimpleBar from 'simplebar-react';

type SimpleBarProps = ComponentProps<typeof SimpleBar>;

type AppScrollbarProps = SimpleBarProps & {
  children: ReactNode;
  className?: string;
};

const AppScrollbar: React.FC<AppScrollbarProps> = ({
  children,
  className = '',
  ...others
}) => {
  return (
    <SimpleBar className={className} style={{ maxHeight: '100%' }} {...others}>
      {children}
    </SimpleBar>
  );
};

export default AppScrollbar;
