import React from 'react';

import { Avatar, Flex, Typography } from 'antd';
import { getPostIcon } from '@unpod/helpers/PermissionHelper';
import { getFirstLetter } from '@unpod/helpers/StringHelper';
import { CONTENT_TYPE_ICONS } from '@unpod/constants';
import {
  EvalButtonWrapper,
  StyledContent,
  StyledDescription,
  StyledHubRow,
  StyledIconCircle,
  StyledOrganizationContainer,
  StyledPrivacyIcon,
  StyledRoot,
  StyledTitleWrapper,
} from './index.styled';
import { useIntl } from 'react-intl';
import type { KnowledgeBase } from '@unpod/constants/types';
import GenerateEvalButton from '../../../modules/GenerateEvalButton/GenerateEvalButton';
import { AppStatusBadge } from '../../AppStatusBadge';

const { Text, Title } = Typography;

const TYPE_COLORS = {
  table: {
    color: '#34c759',
    bg: 'rgba(110, 232, 140, 0.12)',
    icon: '#34c759',
    circle: 'rgba(110, 232, 140, 0.12)',
  },
  email: {
    color: '#ef4437',
    bg: 'rgba(242, 173, 77, 0.12)',
    icon: '#ef4437',
    circle: 'rgba(239, 68, 55, 0.14)',
  },
  contact: {
    color: '#af52de',
    bg: 'rgba(202, 122, 243, 0.12)',
    icon: '#af52de',
    circle: 'rgba(202, 122, 243, 0.12)',
  },
  document: {
    color: '#5990f8',
    bg: 'rgba(66, 146, 233, 0.14)',
    icon: '#5990f8',
    circle: 'rgba(66, 146, 233, 0.14)',
  },
};

type GridItemProps = {
  data: KnowledgeBase;
  onCardClick: (item: KnowledgeBase) => void;
  type?: string;
  reCallAPI: () => void;
};

const GridItem = ({ data, onCardClick, type, reCallAPI }: GridItemProps) => {
  const iconComponent =
    CONTENT_TYPE_ICONS[data.content_type as keyof typeof CONTENT_TYPE_ICONS] ??
    CONTENT_TYPE_ICONS.document;
  const { formatMessage } = useIntl();
  const typeInfo = TYPE_COLORS[
    data.content_type as keyof typeof TYPE_COLORS
  ] || {
    color: '#6c4ad3',
    bg: 'rgba(138,119,255,0.12)',
    icon: '#6c4ad3',
    circle: 'rgba(138,119,255,0.14)',
  };

  return (
    <StyledRoot onClick={() => onCardClick(data)}>
      <Flex align="center" justify="space-between">
        <StyledIconCircle $bg={typeInfo.circle}>
          {React.isValidElement(iconComponent)
            ? React.cloneElement(
                iconComponent as React.ReactElement<{ color?: string }>,
                {
                  color: typeInfo.icon,
                },
              )
            : null}
        </StyledIconCircle>

        {type === 'kb' && data.content_type !== 'evals' && (
          <EvalButtonWrapper>
            {data?.evals_info?.gen_status !== 'pending' ||
            data?.evals_info?.gen_status === undefined ? (
              <GenerateEvalButton
                token={data.token}
                force={data.has_evals as boolean}
                text={
                  data.has_evals ? 'common.refresh' : 'common.generateEvals'
                }
                reCallAPI={reCallAPI}
              />
            ) : (
              <AppStatusBadge
                status={data?.evals_info?.gen_status}
                name={data?.evals_info?.gen_status}
              />
            )}
          </EvalButtonWrapper>
        )}
      </Flex>

      <StyledContent>
        <StyledTitleWrapper>
          <Title level={5} className="title" ellipsis={{ tooltip: data.name }}>
            {data.name}
          </Title>
        </StyledTitleWrapper>
        {/* <StyledTypeLabel $color={typeInfo.color} $bg={typeInfo.bg}>
          {data.content_type?.charAt(0).toUpperCase() +
            data.content_type?.slice(1)}
        </StyledTypeLabel> */}

        <StyledDescription>
          {data.description ||
            formatMessage({ id: 'knowledgeBase.description' })}
        </StyledDescription>

        {/* <StyledDivider /> */}
      </StyledContent>

      <StyledHubRow>
        <StyledOrganizationContainer>
          <Avatar
            style={{
              backgroundColor: data.organization?.logo
                ? ''
                : data.organization?.color,
              marginRight: 8,
            }}
            src={data.organization?.logo}
            size={24}
          >
            {getFirstLetter(data.organization?.name ?? '')}
          </Avatar>
          <Text style={{ fontSize: 13, marginTop: 2 }}>
            {data.organization?.name}
          </Text>
        </StyledOrganizationContainer>
        <StyledPrivacyIcon>
          {getPostIcon(data?.privacy_type ?? '')}
        </StyledPrivacyIcon>
      </StyledHubRow>
    </StyledRoot>
  );
};

export default GridItem;
