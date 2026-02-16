import React, { ReactNode } from 'react';
import { Row } from 'antd';

type AppGridContainerProps = {
  children?: ReactNode;
  gutter?: number | [number, number];
  align?: 'top' | 'middle' | 'bottom';
  justify?: 'start' | 'end' | 'center' | 'space-around' | 'space-between';
  wrap?: boolean;};

const AppGridContainer: React.FC<AppGridContainerProps> = ({
  children,
  align,
  justify,
  gutter = 24,
  wrap,
}) => {
  return (
    <Row gutter={gutter} align={align} justify={justify} wrap={wrap}>
      {children}
    </Row>
  );
};

export default AppGridContainer;
