import React from 'react';
import type { ButtonProps } from 'antd';
import { Button } from 'antd';
import { useIntl } from 'react-intl';
import styled from 'styled-components';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';

type GenerateEvalButtonProps = {
  type: 'pilot' | 'Knowledgebase';
  token?: string;
  buttonType?: ButtonProps['type'];
  padding?: boolean;
  size?: ButtonProps['size'];
  onClick?: (response: { response: any }) => void;
  [key: string]: unknown;
};

interface StyledButtonProps extends ButtonProps {
  $padding?: boolean;
}

export const StyledButton = styled(Button)<StyledButtonProps>`
  display: flex;
  padding-right: ${({ $padding }) => ($padding ? '4px' : '12px')} !important;
  padding-left: ${({ $padding }) => ($padding ? '4px' : '12px')} !important;
  border-color: ${({ theme }) => theme.palette.primary};

  color: ${({ theme, type }) => type != 'primary' && theme.palette.primary};

  &:hover {
    background-color: ${({ theme, type }) =>
      type === 'text' && theme.palette.primary} !important;
    color: ${({ theme, type }) =>
      type === 'text' && theme.palette.common.white} !important;
  }
`;

const GenerateEvalButton: React.FC<GenerateEvalButtonProps> = ({
  type,
  token,
  buttonType = 'text',
  size = 'small',
  padding = false,
  onClick: userOnClick,
  ...rest
}) => {
  const { formatMessage } = useIntl();
  const infoViewActionsContext = useInfoViewActionsContext();

  const payload = {
    type,
    kn_token: type === 'Knowledgebase' ? token : '',
    pilot_handle: type === 'pilot' ? token : '',
  };

  const onClick = (e: React.MouseEvent<HTMLElement>) => {
    e.stopPropagation();

  /* postDataApi(
      'core/knowledgebase-evals/fetch-evals/',
      infoViewActionsContext,
      payload,
    )
      .then((fetchResponse) => {
        infoViewActionsContext.showMessage(
          fetchResponse.message || 'Eval fetched successfully',
        );
        if (userOnClick) userOnClick({ response: fetchResponse });
      })
      .catch((fetchError) => {
        infoViewActionsContext.showError(
          fetchError.message || 'Failed to fetch eval',
        );
      });*/

    postDataApi(
      'core/knowledgebase-evals/generate/',
      infoViewActionsContext,
      payload,
    )
      .then((response) => {
        const res = response as { message?: string };

        infoViewActionsContext.showMessage(
          res.message || 'Eval generated successfully',
        );
      })
      .catch((response) => {
        const res = response as { message?: string };

        infoViewActionsContext.showError(
          res.message || 'Failed to generate eval',
        );
      });
  };

  return (
    <StyledButton
      size={size}
      shape="round"
      onClick={onClick}
      type={buttonType}
      {...rest}
      $padding={padding}
    >
      {formatMessage({ id: 'common.generateEvals' })}
    </StyledButton>
  );
};

export default GenerateEvalButton;
