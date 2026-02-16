
import { useState } from 'react';
import { AiFillYoutube } from 'react-icons/ai';
import YouTube, { YouTubeProps } from 'react-youtube';
import AppImage from '../../next/AppImage';

import {
  StyledImageContainer,
  StyledIPlayBtnWrapper,
  StyledVideoContainer,
  StyledVideoWrapper,
} from './index.styled';

const opts: YouTubeProps['opts'] = {
  height: '315',
  width: '560',
};

type YouTubeDimension = NonNullable<
  NonNullable<YouTubeProps['opts']>['height']
>;

type AppYoutubeVideoProps = YouTubeProps & {
  videoId: string;
  height?: YouTubeDimension;
  width?: YouTubeDimension;};

const AppYoutubeVideo: React.FC<AppYoutubeVideoProps> = ({
  videoId,
  height,
  width,
  ...restProps
}) => {
  const [showVideo, setShowVideo] = useState(false);
  const videoThumbnail = `https://img.youtube.com/vi/${videoId}/0.jpg`;

  const onReady: YouTubeProps['onReady'] = (event) => {
    event.target.playVideo();
  };

  const imageHeight = typeof height === 'string' ? Number(height) : height;
  const imageWidth = typeof width === 'string' ? Number(width) : width;

  return (
    <StyledVideoContainer style={{ width }}>
      <StyledImageContainer>
        <AppImage
          src={videoThumbnail}
          alt="Youtube Video"
          height={imageHeight}
          width={imageWidth}
          layout="responsive"
        />
        {!showVideo && (
          <StyledIPlayBtnWrapper>
            <AiFillYoutube
              className="play-button"
              fontSize={60}
              onClick={() => setShowVideo(true)}
            />
          </StyledIPlayBtnWrapper>
        )}
      </StyledImageContainer>

      {showVideo && (
        <StyledVideoWrapper>
          <YouTube
            loading="lazy"
            videoId={videoId}
            opts={{ ...opts, height, width }}
            onReady={onReady}
            {...restProps}
          />
        </StyledVideoWrapper>
      )}
    </StyledVideoContainer>
  );
};

export default AppYoutubeVideo;
