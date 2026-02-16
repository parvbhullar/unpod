import React, { useEffect, useRef } from 'react';

import {
  StyledAudioPlayer,
  StyledAudioTitle,
  StyledAvatarWrapper,
  StyledCanvas,
  StyledMeta,
  StyledMusicWrapper,
  StyledMuxPlayer,
  StyledPlayerBody,
  StyledPlayerInfo,
  StyledUserBar,
} from './index.styled';
import { useAuthContext } from '@unpod/providers';
import { useTheme } from 'styled-components';
import { Typography } from 'antd';
import AppImage from '../../next/AppImage';
import { MdPlayCircleOutline } from 'react-icons/md';
import { getImageUrl } from '@unpod/helpers/UrlHelper';
import type MuxPlayerElement from '@mux/mux-player';

type MediaInfo = {
  playback_id: string;
  media_id?: string;};

type AppAudioPlayerProps = {
  title?: string;
  subTitle?: string;
  media: MediaInfo;
  poster?: string;};

type MuxPlayerHandle = MuxPlayerElement & {
  media?: { nativeEl?: HTMLMediaElement };
  play?: () => void;
};

const AppAudioPlayer: React.FC<AppAudioPlayerProps> = ({
  title,
  subTitle,
  media,
  poster,
}) => {
  const theme = useTheme();
  const { user } = useAuthContext();
  const playerRef = useRef<MuxPlayerHandle | null>(null);
  const waveformRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const waveformCanvas = waveformRef.current;
    if (!waveformCanvas) return;
    const waveformCtx = waveformCanvas.getContext('2d');
    if (!waveformCtx) return;
    const canvas = waveformCanvas;
    const ctx = waveformCtx;
    const video = playerRef.current?.media?.nativeEl;
    if (!video) return;

    const audioCtx = new AudioContext();
    const analyser = audioCtx.createAnalyser();
    const source = audioCtx.createMediaElementSource(video);
    source.connect(analyser);
    analyser.connect(audioCtx.destination);

    const visualizeWaveform = () => {
      const WIDTH = 600;
      const HEIGHT = 115;
      analyser.fftSize = 2048;
      const bufferLength = analyser.fftSize;

      // We can use Float32Array instead of Uint8Array if we want higher precision
      const dataArray = new Uint8Array(bufferLength);

      ctx.clearRect(0, 0, WIDTH, HEIGHT);

      const draw = () => {
        requestAnimationFrame(draw);

        analyser.getByteTimeDomainData(dataArray);

        ctx.fillStyle = '#E4E1FF';
        ctx.fillRect(0, 0, WIDTH, HEIGHT);

        ctx.lineWidth = 2;
        ctx.strokeStyle = theme.palette.primary;
        ctx.beginPath();

        const sliceWidth = WIDTH / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const v = dataArray[i] / 128.0;
          const y = (v * HEIGHT) / 2;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }

          x += sliceWidth;
        }

        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
      };

      draw();
    };

    visualizeWaveform();
    video.addEventListener('play', visualizeWaveform, false);

    return () => {
      video.removeEventListener('play', visualizeWaveform, false);
    };
  }, [media.playback_id, theme.palette.primary]);

  const onPlayClick = () => {
    playerRef?.current?.play?.();
  };

  return (
    <StyledAudioPlayer>
      <StyledPlayerBody>
        <StyledPlayerInfo>
          <StyledUserBar>
            <StyledAvatarWrapper onClick={onPlayClick}>
              <MdPlayCircleOutline fontSize={36} />
            </StyledAvatarWrapper>

            <StyledMeta>
              <StyledAudioTitle level={3}>{title}</StyledAudioTitle>
              {subTitle && (
                <Typography.Paragraph type="secondary">
                  {subTitle}
                </Typography.Paragraph>
              )}
            </StyledMeta>
          </StyledUserBar>

          <StyledCanvas
            id={`waveform-${media.playback_id}`}
            ref={waveformRef}
          />
        </StyledPlayerInfo>

        <StyledMusicWrapper>
          <AppImage
            src={getImageUrl('music.svg')}
            alt="music"
            layout="fill"
            objectFit="cover"
          />
        </StyledMusicWrapper>
      </StyledPlayerBody>
      <StyledMuxPlayer
        ref={playerRef}
        // title={title}
        streamType="on-demand"
        playbackId={media.playback_id}
        poster={poster}
        metadata={{
          video_id: media.media_id,
          video_title: title,
          viewer_user_id: user?.user_token || 'guest',
        }}
        audio
        className="mux-player audio-player"
        envKey={process.env.muxEnvKey}
      ></StyledMuxPlayer>
    </StyledAudioPlayer>
  );
};

export default AppAudioPlayer;
