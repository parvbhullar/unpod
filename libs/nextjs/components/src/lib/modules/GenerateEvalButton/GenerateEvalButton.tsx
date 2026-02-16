import React from 'react';
import type { ButtonProps } from 'antd';
import { Button } from 'antd';
import { useIntl } from 'react-intl';
import styled from 'styled-components';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';
import type { Spaces } from '@unpod/constants/types';

type GenerateEvalButtonProps = {
  type?: 'pilot' | 'knowledgebase';
  token?: string;
  buttonType?: ButtonProps['type'];
  padding?: boolean;
  size?: ButtonProps['size'];
  onClick?: (response: { response: Spaces }) => void;
  text: string;
  force: boolean;
  reCallAPI?: () => void;
  [key: string]: unknown;
};

type StyledButtonProps = {
  $padding?: boolean;
};

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
  type = 'knowledgebase',
  token,
  buttonType = 'text',
  size = 'small',
  padding = false,
  onClick: userOnClick,
  force = false,
  text = 'common.generateEvals',
  reCallAPI,
  ...rest
}) => {
  const { formatMessage } = useIntl();
  const infoViewActionsContext = useInfoViewActionsContext();

  const payload = {
    type,
    kn_token: type === 'knowledgebase' ? token : '',
    pilot_handle: type === 'pilot' ? token : '',
    force: force,
  };

  const onClick = (e: React.MouseEvent<HTMLElement>) => {
    e.stopPropagation();
    postDataApi<Spaces[]>(
      'core/knowledgebase-evals/generate/',
      infoViewActionsContext,
      payload,
    )
      .then((res) => {
        if (userOnClick) userOnClick({ response: res?.data[0] });
        reCallAPI?.();
        infoViewActionsContext.showMessage(
          res.message || 'Eval generated successfully',
        );
      })
      .catch((error) => {
        infoViewActionsContext.showError(
          error.message || 'Failed to generate eval',
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
      {formatMessage({ id: text })}
    </StyledButton>
  );
};

export default GenerateEvalButton;
