import { type ReactNode } from 'react';
import {
  StyledDescription,
  StyledIconWrapper,
  StyledRoot,
  StyledTitle,
} from './index.styled';

type TabCardProps = {
  item: { icon?: ReactNode; title?: ReactNode; description?: ReactNode };
  [key: string]: any;
};

const TabCard = ({ item, ...restProps }: TabCardProps) => {
  return (
    <StyledRoot {...restProps}>
      <StyledIconWrapper>{item.icon}</StyledIconWrapper>
      <StyledTitle level={5}>{item.title}</StyledTitle>
      <StyledDescription>{item.description}</StyledDescription>
    </StyledRoot>
  );
};

export default TabCard;
