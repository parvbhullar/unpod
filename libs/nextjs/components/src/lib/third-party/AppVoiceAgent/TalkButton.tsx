import React from 'react';
import { StyledButton } from '../../modules/AppQueryWindow/index.styled';
import { MdArrowForward } from 'react-icons/md';
import {
  ACCESS_ROLE,
  POST_CONTENT_TYPE,
  POST_TYPE,
} from '@unpod/constants/AppEnums';
import {
  postDataApi,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useAgentConnection } from '@unpod/livekit/hooks/useAgentConnection';
import AgentView from './AgentView';
import { useIntl } from 'react-intl';

const TalkButton = ({
  form,
  attachments,
  pilot,
  selectedSpace,
  privacyType,
  executionType,
  userList,
  knowledgeBases,
  defaultKbs,
  focus,
}) => {
  const { token, updateToken } = useAgentConnection();
  const { visitorId, isAuthenticated } = useAuthContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();

  const savePost = (payload) => {
    if (isAuthenticated && selectedSpace?.token) {
      const requestUrl = `http://localhost:4200/api/token/livekit/`;
      postDataApi(requestUrl, infoViewActionsContext, {
        ...payload,
        space_token: selectedSpace?.token,
      })
        .then((data) => {
          console.log(data.accessToken);
          updateToken(data.accessToken);
        })
        .catch((error) => {
          infoViewActionsContext.showError(error.message);
          // setLoading(false);
        });
    }
  };

  const onQuerySubmit = () => {
    const values = form.getFieldsValue();
    let payload = {
      post_type: POST_TYPE.ASK,
      content_type: POST_CONTENT_TYPE.TEXT,
      session_user: visitorId,
      pilot: pilot?.slug || '',
      focus: focus,
      execution_type: executionType || '',
      knowledge_bases: defaultKbs
        ? [...defaultKbs, ...knowledgeBases]
        : knowledgeBases,
    };

    if (isAuthenticated) {
      const { content, ...rest } = values;
      payload = {
        post_type: POST_TYPE.ASK,
        content_type: POST_CONTENT_TYPE.TEXT,
        privacy_type: privacyType,
        pilot: pilot?.slug || '',
        focus: focus,
        execution_type: executionType || '',
        knowledge_bases: defaultKbs
          ? [...defaultKbs, ...knowledgeBases]
          : knowledgeBases,
        user_list:
          privacyType === 'shared'
            ? userList.filter((user) => user.role_code !== ACCESS_ROLE.OWNER)
            : [],
        ...rest,
      };
    }

    savePost(payload);
  };

  if (token) {
    return <AgentView token={token} />;
  } else {
    return (
      <StyledButton type="primary" shape="round" onClick={onQuerySubmit}>
        {formatMessage({ id: 'common.talk' })} <MdArrowForward fontSize={18} />
      </StyledButton>
    );
  }
};

export default TalkButton;
