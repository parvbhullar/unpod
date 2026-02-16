import React from 'react';
import styled from 'styled-components';

export type AppDeleteIconProps = React.HTMLAttributes<HTMLSpanElement> & {
  className?: string;};

const StyledDeleteWrapper = styled.span`
  &.red {
    color: red !important;
  }
`;

export const AppDeleteIcon: React.FC<AppDeleteIconProps> = ({
  className,
  ...props
}) => {
  return (
    <StyledDeleteWrapper
      className={`anticon anticon-delete ${className || ''}`}
      {...props}
    >
      <svg
        width="21"
        height="21"
        viewBox="0 0 21 21"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <g clipPath="url(#clip0_713_26)">
          <path
            d="M17.7188 4.59375H3.28125"
            stroke="currentColor"
            strokeWidth="1.3125"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M8.53125 8.53125V13.7812"
            stroke="currentColor"
            strokeWidth="1.3125"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M12.4688 8.53125V13.7812"
            stroke="currentColor"
            strokeWidth="1.3125"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M16.4062 4.59375L16.1063 16.9715C16.1063 17.1456 16.0371 17.3125 15.9141 17.4356C15.791 17.5586 15.6241 17.6278 15.45 17.6278H5.58711C5.41306 17.6278 5.24614 17.5586 5.12307 17.4356C5 17.3125 4.93086 17.1456 4.93086 16.9715L4.59375 4.59375"
            stroke="currentColor"
            strokeWidth="1.3125"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M13.7812 4.59375V3.28125C13.7812 2.93315 13.643 2.59931 13.3968 2.35317C13.1507 2.10703 12.8168 1.96875 12.4688 1.96875H8.53125C8.18315 1.96875 7.84931 2.10703 7.60317 2.35317C7.35703 2.59931 7.21875 2.93315 7.21875 3.28125V4.59375"
            stroke="currentColor"
            strokeWidth="1.3125"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>
        <defs>
          <clipPath id="clip0_713_26">
            <rect width="21" height="21" fill="white" />
          </clipPath>
        </defs>
      </svg>
    </StyledDeleteWrapper>
  );
};

export default AppDeleteIcon;
