import React from 'react';
import AppVideoPlayer from './AppVideoPlayer';
import AppAudioPlayer from './AppAudioPlayer';

type Media = {
  media_type: 'audio' | 'video';
  playback_id: string;
  media_id?: string;};

type AppMediaPlayerProps = {
  title?: string;
  subTitle?: string;
  media: Media;
  poster?: string;};

const AppMediaPlayer: React.FC<AppMediaPlayerProps> = ({
  title,
  subTitle,
  media,
  poster,
}) => {
  return (
    media &&
    (media.media_type === 'audio' ? (
      <AppAudioPlayer
        title={title}
        subTitle={subTitle}
        media={media}
        poster={poster}
      />
    ) : (
      <AppVideoPlayer title={title} media={media} poster={poster} />
    ))
  );
};

export default React.memo(AppMediaPlayer);
