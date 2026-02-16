import React, { useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import AppMiniWindow from '../../common/AppMiniWindow';
import CreateNote from './CreateNote';
import UploadPodcast from './UploadPodcast';
import CreateStream from './CreateStream';
import { useRouter } from 'next/navigation';
import KnowledgeBase from './KnowledgeBase';
import { useIntl } from 'react-intl';

const AppPodcast = ({
  startPodcast,
  setStartPodcast,
  currentSpace,
  currentPost,
  isEdit,
  onAddPostItem,
  openLocally,
  sidebarRef,
}) => {
  const [creatingPost, setCreatingPost] = useState(false);
  const router = useRouter();
  const { formatMessage } = useIntl();
  // const [createdPodcast, setCreatedPodcast] = useState(null);

  /* const onLinkClick = useCallback(() => {
    if (createdPodcast) {
      const postUrl = `/post/${createdPodcast?.slug}/`;
      setStartPodcast('');
      setCreatedPodcast(null);
      router.push(postUrl);
    }
  }, [createdPodcast, router]);*/

  const viewData = useMemo(() => {
    if (startPodcast) {
      switch (startPodcast) {
        case 'create-note':
          return {
            drawerTitle: formatMessage({ id: 'podcast.writePost' }),
            title: formatMessage({ id: 'podcast.notePostedSuccess' }),
          };

        case 'upload-podcast':
          return {
            drawerTitle: formatMessage({ id: 'podcast.uploadMedia' }),
            title: formatMessage({ id: 'podcast.uploadSuccess' }),
          };

        case 'video_stream':
          return {
            drawerTitle: formatMessage({ id: 'podcast.stream' }),
            title: formatMessage({ id: 'podcast.videoStreaming' }),
          };

        case 'knowledge-base':
          return {
            drawerTitle: formatMessage({ id: 'podcast.addKnowledgeBase' }),
            title: formatMessage({ id: 'podcast.addKnowledgeBaseTitle' }),
          };

        case 'audio_stream':
          return {
            drawerTitle: formatMessage({ id: 'podcast.stream' }),
            title: formatMessage({ id: 'podcast.audioStreaming' }),
          };

        default:
          return {
            drawerTitle: formatMessage({ id: 'podcast.schedule' }),
            title: formatMessage({ id: 'podcast.scheduleSuccess' }),
          };
      }
    }
  }, [startPodcast, formatMessage]);

  const onSpaceSaved = (response) => {
    onAddPostItem(response.data);
    if (sidebarRef?.current) {
      sidebarRef.current?.reloadPosts();
    }
    if (startPodcast === 'audio_stream' || startPodcast === 'video_stream') {
      router.push(
        `/${response.data.organization.domain_handle}/${response.data.space.slug}/${response.data.slug}/stream`,
      );
    }
    setStartPodcast('');
  };

  const getPostByType = (startPodcast) => {
    switch (startPodcast) {
      case 'create-note':
        return (
          <CreateNote
            setCreatingPost={setCreatingPost}
            onSaved={onSpaceSaved}
            currentSpace={currentSpace}
            isEdit={isEdit}
            currentPost={currentPost}
          />
        );
      case 'upload-podcast':
        return (
          <UploadPodcast
            setCreatingPost={setCreatingPost}
            onSaved={onSpaceSaved}
            isEdit={isEdit}
            currentSpace={currentSpace}
            currentPost={currentPost}
          />
        );
      case 'knowledge-base':
        return (
          <KnowledgeBase
            setCreatingPost={setCreatingPost}
            onSaved={onSpaceSaved}
            isEdit={isEdit}
            currentSpace={currentSpace}
            currentPost={currentPost}
          />
        );
      case 'video_stream':
      case 'audio_stream':
        return (
          <CreateStream
            setCreatingPost={setCreatingPost}
            onSaved={onSpaceSaved}
            isEdit={isEdit}
            currentSpace={currentSpace}
            currentPost={currentPost}
          />
        );
      default:
        return (
          <CreateNote
            setCreatingPost={setCreatingPost}
            onSaved={onSpaceSaved}
            isEdit={isEdit}
            currentSpace={currentSpace}
            currentPost={currentPost}
          />
        );
    }
  };

  return (
    <AppMiniWindow
      creatingPost={creatingPost}
      setCreatingPost={creatingPost}
      open={!!startPodcast}
      title={viewData?.drawerTitle}
      onClose={() => setStartPodcast('')}
      openLocally={openLocally}
    >
      {!!startPodcast && getPostByType(startPodcast)}
    </AppMiniWindow>
  );
};

AppPodcast.propTypes = {
  startPodcast: PropTypes.string,
  setStartPodcast: PropTypes.func,
  currentSpace: PropTypes.object,
  currentPost: PropTypes.object,
  openLocally: PropTypes.bool,
};

export default AppPodcast;
