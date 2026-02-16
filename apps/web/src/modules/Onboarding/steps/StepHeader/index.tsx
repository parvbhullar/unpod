import React from 'react';
import { useIntl } from 'react-intl';
import { StyledParagraph, StyledRoot, StyledTitle } from './index.styled';

const StepHeader = () => {
  const { formatMessage } = useIntl();

  return (
    <StyledRoot>
      <StyledTitle level={3} ellipsis={true}>
        {formatMessage({ id: 'identityOnboarding.createVoiceIdentity' })}
      </StyledTitle>
      <StyledParagraph>
        {formatMessage({ id: 'identityOnboarding.giveBusinessVoice' })}
      </StyledParagraph>
    </StyledRoot>
  );
};

export default StepHeader;
