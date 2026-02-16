import React from 'react';
import {
  StyledContent,
  StyledParagraph,
  StyledRoot,
  StyledTitle,
} from './index.styled';
import { useIntl } from 'react-intl';
import type { SectionMetricsItem } from '@unpod/constants/types';

type MetricsCardProps = {
  data: SectionMetricsItem;
};

const MetricsCard: React.FC<MetricsCardProps> = ({ data }) => {
  const { formatMessage } = useIntl();

  return (
    <StyledRoot>
      <StyledContent>
        <StyledTitle>{data.title}</StyledTitle>
        <StyledParagraph>
          {formatMessage({ id: data.description })}
        </StyledParagraph>
      </StyledContent>
    </StyledRoot>
  );
};

export default MetricsCard;
