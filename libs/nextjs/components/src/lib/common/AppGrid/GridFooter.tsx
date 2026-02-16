import React from 'react';
import { Progress } from 'antd';
import { StyledListFooter, StyledLoaderProgress } from './index.styled';

type GridFooterProps = {
  loading?: boolean;
  footerText?: string;};

const GridFooter: React.FC<GridFooterProps> = ({ loading, footerText }) => {
  if (loading) {
    return (
      <StyledLoaderProgress>
        <Progress percent={30} />
        <span>Loading...</span>
      </StyledLoaderProgress>
    );
  } else {
    return (
      <StyledListFooter>
        <p>{footerText}</p>
      </StyledListFooter>
    );
  }
};

export default GridFooter;
