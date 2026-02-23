import styled from 'styled-components';
import type {ComponentPropsWithoutRef} from 'react';

const StyledFormFooter = styled.div`
  background-color: ${({theme}) => theme.palette.background.default};
  border-top: 1px solid ${({theme}) => theme.border.color};
  width: 100%;
  z-index: 2;
  display: flex;
  justify-content: flex-end;
  margin: auto 0 !important;
  padding-top: 16px !important;
  padding-right: 24px !important;

  & .ant-btn {
    min-width: 120px;

    &:last-child {
      margin-left: 10px;
    }
  }
`;

type DrawerFooterProps = ComponentPropsWithoutRef<'div'>;

export const DrawerFooter = (props: DrawerFooterProps) => {
  return <StyledFormFooter {...props} />;
};

export default DrawerFooter;
