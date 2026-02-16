import React from 'react';

export type AppIconProps = React.HTMLAttributes<HTMLSpanElement>;

export const AppInvestorIcon: React.FC<AppIconProps> = (props) => {
  return (
    <span className="anticon anticon-investor" {...props}>
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M32 14C32 12.1401 32 11.2101 31.7956 10.4471C31.2408 8.37653 29.6235 6.75925 27.5529 6.20445C26.7899 6 25.8599 6 24 6C22.1401 6 21.2101 6 20.4471 6.20445C18.3765 6.75925 16.7592 8.37653 16.2044 10.4471C16 11.2101 16 12.1401 16 14M10.4 42H37.6C39.8402 42 40.9603 42 41.816 41.564C42.5686 41.1805 43.1805 40.5686 43.564 39.816C44 38.9603 44 37.8402 44 35.6V20.4C44 18.1598 44 17.0397 43.564 16.184C43.1805 15.4314 42.5686 14.8195 41.816 14.436C40.9603 14 39.8402 14 37.6 14H10.4C8.15979 14 7.03968 14 6.18404 14.436C5.43139 14.8195 4.81947 15.4314 4.43597 16.184C4 17.0397 4 18.1598 4 20.4V35.6C4 37.8402 4 38.9603 4.43597 39.816C4.81947 40.5686 5.43139 41.1805 6.18404 41.564C7.03968 42 8.15979 42 10.4 42Z"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
};

export default AppInvestorIcon;
