import React from 'react';

export type AppIconProps = React.HTMLAttributes<HTMLSpanElement>;

export const AppDownloadIcon: React.FC<AppIconProps> = (props) => {
  return (
    <span className="anticon anticon-download" {...props}>
      <svg
        width="21"
        height="21"
        viewBox="0 0 21 21"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <g clipPath="url(#clip0_715_54)">
          <path
            d="M10.5 12.4688V3.28125"
            stroke="currentColor"
            strokeWidth="1.3125"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M17.7188 12.4688V17.0625C17.7188 17.2365 17.6496 17.4035 17.5265 17.5265C17.4035 17.6496 17.2365 17.7188 17.0625 17.7188H3.9375C3.76345 17.7188 3.59653 17.6496 3.47346 17.5265C3.35039 17.4035 3.28125 17.2365 3.28125 17.0625V12.4688"
            stroke="currentColor"
            strokeWidth="1.3125"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M13.7812 9.1875L10.5 12.4688L7.21875 9.1875"
            stroke="currentColor"
            strokeWidth="1.3125"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>
        <defs>
          <clipPath id="clip0_715_54">
            <rect width="21" height="21" fill="white" />
          </clipPath>
        </defs>
      </svg>
    </span>
  );
};

export default AppDownloadIcon;
