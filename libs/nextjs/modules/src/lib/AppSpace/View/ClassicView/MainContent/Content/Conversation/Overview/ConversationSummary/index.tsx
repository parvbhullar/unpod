import { Fragment, useState } from 'react';
import {
  StyledCard,
  StyledDateHeader,
  StyledDateSection,
  StyledEditButton,
} from './index.styled';
import { Typography } from 'antd';
import { MdEdit } from 'react-icons/md';
import SummaryEditar from './SummaryEditar';
import AppMarkdownViewer from '@unpod/components/third-party/AppMarkdownViewer';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';

const { Text } = Typography;

const ConversationSummary = ({
  currentPost,
  setCurrentPost,
  token,
}: {
  currentPost: any;
  setCurrentPost: (post: any) => void;
  token: any;
}) => {
  const mobileScreen = useMediaQuery(MobileWidthQuery);

  const [isEditing, setIsEditing] = useState(false);
  const SummaryEditarAny = SummaryEditar as any;

  return (
    <StyledDateSection>
      <StyledDateHeader strong>CONVERSATION SUMMARY</StyledDateHeader>
      <StyledCard>
        {isEditing ? (
          <SummaryEditarAny
            currentPost={currentPost}
            setCurrentPost={setCurrentPost}
            setIsEditing={setIsEditing}
            token={token}
          />
        ) : (
          <Fragment>
            {currentPost.content ? (
              <AppMarkdownViewer markdown={currentPost.content} />
            ) : (
              <Text>No conversation summary</Text>
            )}
            <StyledEditButton onClick={() => setIsEditing(true)} type="default">
              <MdEdit size={13} />
              {!mobileScreen && 'Edit'}
            </StyledEditButton>
          </Fragment>
        )}
      </StyledCard>
    </StyledDateSection>
  );
};

export default ConversationSummary;
