import React, {ReactNode} from 'react';
import {INPUT_TYPE_ICONS, INPUT_TYPES} from '@unpod/constants';
import {StyledDivider, StyledList, StyledListItem} from './index.styled';
import AppPopover from '../AppPopover';
import {useIntl} from 'react-intl';

type InputType = {
  type: string;
  placeholder: string;
  [key: string]: unknown;
};

type AppInputSelectorProps = {
  onSelect: (input: InputType) => void;
  allowFormInput?: boolean;
  excludes?: string[];
  children?: ReactNode;
  [key: string]: unknown;
};

const AppInputSelector: React.FC<AppInputSelectorProps> = ({
                                                             onSelect,
                                                             allowFormInput = false,
                                                             excludes = [],
                                                             ...restProps
                                                           }) => {
  const {formatMessage} = useIntl();
  const allowedTypes = (INPUT_TYPES as InputType[]).filter(
    (input) => !(excludes || []).includes(input.type),
  );

  const content = (
    <StyledList>
      {allowedTypes.map((input, index) =>
        input.type === 'separator' ? (
          <StyledListItem key={index}>
            <StyledDivider/>
          </StyledListItem>
        ) : (
          ((allowFormInput && input.type === 'form') ||
            input.type !== 'form') && (
            <StyledListItem key={index} onClick={() => onSelect(input)}>
              {(INPUT_TYPE_ICONS as Record<string, ReactNode>)[input.type]}{' '}
              {formatMessage({id: input.placeholder})}
            </StyledListItem>
          )
        ),
      )}
    </StyledList>
  );

  return <AppPopover content={content} {...restProps} />;
};

export default AppInputSelector;
