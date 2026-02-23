import {StyledMuxPlayer} from './index.styled';
import {useAuthContext} from '@unpod/providers';

type MediaInfo = {
  playback_id: string;
  media_id?: string;
};

type AppVideoPlayerProps = {
  title?: string;
  media: MediaInfo;
  poster?: string;
};

const AppVideoPlayer: React.FC<AppVideoPlayerProps> = ({
                                                         title,
                                                         media,
                                                         poster,
                                                       }) => {
  const {user} = useAuthContext();

  return (
    <StyledMuxPlayer
      title={title}
      streamType="on-demand"
      playbackId={media.playback_id}
      poster={poster}
      metadata={{
        video_id: media.media_id,
        video_title: title,
        viewer_user_id: user?.user_token || 'guest',
      }}
      className="mux-player video-player"
      envKey={process.env.muxEnvKey}
    />
  );
};

export default AppVideoPlayer;
