import React from 'react';
import {
  StyledFPContainer,
  StyledFPInnerContainer,
  StyledFPSubTitle,
  StyledFPTitle,
} from './FirstPersonDisplay.styled';
import { Typography } from 'antd';

export const FirstPersonDisplay = React.memo(() => {
  return (
    <StyledFPContainer data-testid="first_person_img">
      <StyledFPInnerContainer>
        <StyledFPTitle level={4}>Welcome!</StyledFPTitle>
        <StyledFPSubTitle strong>You’re the first one here.</StyledFPSubTitle>
        <Typography.Paragraph>
          Sit back and relax till the others join.
        </Typography.Paragraph>
      </StyledFPInnerContainer>
    </StyledFPContainer>
  );
});
