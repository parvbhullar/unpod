import React, {ReactNode} from 'react';
import Link, {LinkProps} from 'next/link';

type AppLinkProps = Omit<LinkProps, 'href'> & {
  href: string;
  children: ReactNode;
  disabled?: boolean;
  [key: string]: unknown;
};

const AppLink: React.FC<AppLinkProps> = ({href, children, ...rest}) => {
  // if (rest.disabled) {
  //   return <span>{children}</span>;
  // }
  return (
    <Link href={href} {...rest}>
      {children}
    </Link>
  );
};

export default AppLink;
