import React from 'react';

export type AppIconProps = React.HTMLAttributes<HTMLSpanElement>;

export const AppBusinessIcon: React.FC<AppIconProps> = (props) => {
  return (
    <span className="anticon anticon-business" {...props}>
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M22 22H12.4C10.1598 22 9.03969 22 8.18404 22.436C7.43139 22.8195 6.81947 23.4314 6.43597 24.184C6 25.0397 6 26.1598 6 28.4V42M42 42V12.4C42 10.1598 42 9.03969 41.564 8.18404C41.1805 7.43139 40.5686 6.81947 39.816 6.43597C38.9603 6 37.8402 6 35.6 6H28.4C26.1598 6 25.0397 6 24.184 6.43597C23.4314 6.81947 22.8195 7.43139 22.436 8.18404C22 9.03969 22 10.1598 22 12.4V42M44 42H4M29 14H35M29 22H35M29 30H35"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
};

export default AppBusinessIcon;
