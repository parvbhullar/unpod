import type { ReactNode } from 'react';
import { memo } from 'react';

import { Button } from 'antd';
import { PiStarFourBold } from 'react-icons/pi';
import { StyledContainer, StyledSuggestionRoot } from './index.styled';

const suggestions = [
  'Provide a brief Summary',
  'What are the action items?',
  'Suggest a reply',
];

type DocumentFooterProps = {
  children?: ReactNode;
  summary?: ReactNode;
  onSuggestionsClick?: (suggestion: string) => void;
  hideSuggestions?: boolean;
};

const DocumentFooter = ({
  children,
  summary,
  onSuggestionsClick,
  hideSuggestions = false,
}: DocumentFooterProps) => {
  const items = suggestions.filter(
    (suggestion) => (summary && !suggestion.includes('Summary')) || !summary,
  );
  return (
    <StyledSuggestionRoot>
      <StyledContainer>
        {children}
        {!hideSuggestions &&
          items.map((suggestion) => (
            <Button
              key={suggestion}
              type="default"
              shape="round"
              icon={<PiStarFourBold fontSize={18} />}
              onClick={() => onSuggestionsClick?.(suggestion)}
            >
              {suggestion}
            </Button>
          ))}
      </StyledContainer>
    </StyledSuggestionRoot>
  );
};

export default memo(DocumentFooter);
