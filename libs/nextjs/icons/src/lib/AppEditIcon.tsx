import React from 'react';

export type AppIconProps = React.HTMLAttributes<HTMLSpanElement>;

export const AppEditIcon: React.FC<AppIconProps> = (props) => {
  return (
    <span className="anticon anticon-edit" {...props}>
      <svg
        width="21"
        height="21"
        viewBox="0 0 21 21"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M10.5 13.125H7.875V10.5L15.75 2.625L18.375 5.25L10.5 13.125Z"
          stroke="currentColor"
          strokeWidth="1.3125"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M13.7812 4.59375L16.4062 7.21875"
          stroke="currentColor"
          strokeWidth="1.3125"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M17.7188 9.84375V17.0625C17.7188 17.2365 17.6496 17.4035 17.5265 17.5265C17.4035 17.6496 17.2365 17.7188 17.0625 17.7188H3.9375C3.76345 17.7188 3.59653 17.6496 3.47346 17.5265C3.35039 17.4035 3.28125 17.2365 3.28125 17.0625V3.9375C3.28125 3.76345 3.35039 3.59653 3.47346 3.47346C3.59653 3.35039 3.76345 3.28125 3.9375 3.28125H11.1562"
          stroke="currentColor"
          strokeWidth="1.3125"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
};

export default AppEditIcon;
