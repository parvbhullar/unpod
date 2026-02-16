import React from 'react';
import clsx from 'clsx';
import { StyledContent, StyledRoot, StyledStep } from './index.styled';
import { useIntl } from 'react-intl';

type StepHeaderProps = {
  step: number;
  title?: string;
  description?: string;
  activeStep: number;
};

const StepHeader: React.FC<StepHeaderProps> = ({
  step,
  title,
  description,
  activeStep,
}) => {
  const { formatMessage } = useIntl();
  return (
    <StyledRoot>
      <StyledStep
        className={clsx({
          success: step < activeStep,
          active: activeStep === step,
        })}
      >
        {step}
      </StyledStep>
      <StyledContent>
        {title && (
          <div className="step-title">{formatMessage({ id: title })}</div>
        )}
        {description && (
          <div className="step-description">
            {formatMessage({ id: description })}
          </div>
        )}
      </StyledContent>
    </StyledRoot>
  );
};

export default StepHeader;
