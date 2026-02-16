import React from 'react';

export type AppIconProps = React.HTMLAttributes<HTMLSpanElement>;

export const AppViewIcon: React.FC<AppIconProps> = (props) => {
  return (
    <span className="anticon anticon-view" {...props}>
      <svg
        width="21"
        height="21"
        viewBox="0 0 21 21"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M10.5 4.59375C3.9375 4.59375 1.3125 10.5 1.3125 10.5C1.3125 10.5 3.9375 16.4062 10.5 16.4062C17.0625 16.4062 19.6875 10.5 19.6875 10.5C19.6875 10.5 17.0625 4.59375 10.5 4.59375Z"
          stroke="currentColor"
          strokeWidth="1.3125"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M10.5 13.7812C12.3122 13.7812 13.7812 12.3122 13.7812 10.5C13.7812 8.68782 12.3122 7.21875 10.5 7.21875C8.68782 7.21875 7.21875 8.68782 7.21875 10.5C7.21875 12.3122 8.68782 13.7812 10.5 13.7812Z"
          stroke="currentColor"
          strokeWidth="1.3125"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
};

export default AppViewIcon;
