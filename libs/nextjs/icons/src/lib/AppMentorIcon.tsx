import React from 'react';

export type AppIconProps = React.HTMLAttributes<HTMLSpanElement>;

export const AppMentorIcon: React.FC<AppIconProps> = (props) => {
  return (
    <span className="anticon anticon-mentor" {...props}>
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M10 19.9992V32.0214C10 32.7394 10 33.0983 10.1093 33.4152C10.206 33.6955 10.3637 33.9507 10.5712 34.1625C10.8057 34.402 11.1268 34.5626 11.7689 34.8836L22.5689 40.2836C23.0936 40.546 23.356 40.6772 23.6312 40.7288C23.8749 40.7745 24.1251 40.7745 24.3688 40.7288C24.644 40.6772 24.9064 40.546 25.4311 40.2836L36.2311 34.8836C36.8732 34.5625 37.1943 34.402 37.4288 34.1625C37.6363 33.9507 37.794 33.6955 37.8907 33.4152C38 33.0983 38 32.7394 38 32.0214V19.9992M4 16.9992L23.2845 7.35692C23.5468 7.22574 23.678 7.16015 23.8156 7.13434C23.9375 7.11147 24.0625 7.11147 24.1844 7.13434C24.322 7.16015 24.4532 7.22574 24.7155 7.35692L44 16.9992L24.7155 26.6414C24.4532 26.7726 24.322 26.8382 24.1844 26.864C24.0625 26.8868 23.9375 26.8868 23.8156 26.864C23.678 26.8382 23.5468 26.7726 23.2845 26.6414L4 16.9992Z"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
};

export default AppMentorIcon;
