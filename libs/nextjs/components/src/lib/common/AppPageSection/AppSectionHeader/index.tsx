import {
  type HTMLAttributes,
  isValidElement,
  memo,
  type ReactNode,
} from 'react';

import { Typography } from 'antd';
import { StyledExtraWrapper, StyledSectionHeader } from './index.styled';

type AppSectionHeaderProps = HTMLAttributes<HTMLDivElement> & {
  heading?: ReactNode;
  subHeading?: ReactNode;
  description?: ReactNode;
  headerMaxWidth?: number;
  extra?: ReactNode;};

const AppSectionHeader = ({
  heading,
  subHeading,
  description,
  headerMaxWidth = 600,
  extra,
  ...restProps
}: AppSectionHeaderProps) => {
  return (
    (heading || subHeading || description || extra) && (
      <StyledSectionHeader $maxWidth={headerMaxWidth} {...restProps}>
        {heading &&
          (isValidElement(heading) ? (
            heading
          ) : (
            <Typography.Title level={2}>{heading}</Typography.Title>
          ))}

        {subHeading &&
          (isValidElement(subHeading) ? (
            subHeading
          ) : (
            <Typography.Title level={4} className="sub-title">
              {subHeading}
            </Typography.Title>
          ))}

        {description &&
          (isValidElement(description) ? (
            description
          ) : (
            <Typography.Paragraph type="secondary">
              {description}
            </Typography.Paragraph>
          ))}

        {extra && <StyledExtraWrapper>{extra}</StyledExtraWrapper>}
      </StyledSectionHeader>
    )
  );
};

export default memo(AppSectionHeader);
