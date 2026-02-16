import type { ReactNode } from 'react';

import { Row } from 'antd';
import { StyledRoot } from './index.styled';

type FullWidthLayoutProps = {
  children?: ReactNode;};

const FullWidthLayout = ({ children }: FullWidthLayoutProps) => {
  return (
    <StyledRoot>
      <Row align={'middle'} justify="center" className={'h-100'}>
        {children}
      </Row>
    </StyledRoot>
  );
};

export default FullWidthLayout;
