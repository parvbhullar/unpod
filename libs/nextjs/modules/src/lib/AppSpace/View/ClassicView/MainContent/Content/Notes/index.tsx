import React, {Fragment} from 'react';
import PropTypes from 'prop-types';
import {AgentConnectionProvider} from '@unpod/livekit/hooks/useAgentConnection';
import AppPost from '../../../../../../AppPost';
import AddEditThread from './AddEditThread';
import AddNote from './AddNew';
import {StyledContainer, StyledRoot, StyledRow} from '../../index.styled';
import {useAppSpaceActionsContext, useAppSpaceContext,} from '@unpod/providers';

const Notes = ({threadType, setThreadType}) => {
  const {setActiveNote, notesActions} = useAppSpaceActionsContext();
  const {activeNote, currentSpace, token} = useAppSpaceContext();
  const onEditPost = () => {
    if (activeNote) {
      setThreadType(`${activeNote.post_type}_${activeNote.content_type}`);
    }
  };

  const onDataSaved = (data, isNew = false) => {
    setActiveNote(data);
    if (isNew) notesActions.setData((prevData) => [data, ...prevData]);
    else
      notesActions.setData((prevData) => [
        data,
        ...prevData.filter((item) => item.post_id !== data.post_id),
      ]);

    setThreadType('');
  };

  const onAddClick = (key) => {
    setThreadType(key);
    setActiveNote(null);
  };

  return (
    <StyledRoot>
      {threadType ? (
        <AddEditThread
          post={activeNote}
          currentSpace={currentSpace}
          threadType={threadType}
          onDataSaved={onDataSaved}
          setThreadType={setThreadType}
        />
      ) : (
        <Fragment>
          {activeNote ? (
            <AgentConnectionProvider>
              <AppPost
                token={token}
                currentPost={activeNote}
                setCurrentPost={setActiveNote}
                onDeletedPost={() => setActiveNote(null)}
                onEditPost={onEditPost}
              />
            </AgentConnectionProvider>
          ) : (
            <StyledContainer>
              <StyledRow align="middle" justify="center">
                <AddNote onAddClick={onAddClick}/>
              </StyledRow>
            </StyledContainer>
          )}
        </Fragment>
      )}
    </StyledRoot>
  );
};

Notes.displayName = 'NoteDetail';

const {func, object, string} = PropTypes;

Notes.propTypes = {
  currentSpace: object,
  activeNote: object,
  setActiveNote: func,
  setActiveDocument: func,
  threadType: string,
  setThreadType: func,
};

export default Notes;
