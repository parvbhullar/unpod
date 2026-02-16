import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { useRef, useState } from 'react';
import { Button, Tooltip } from 'antd';
import { MdOutlinePause, MdOutlinePlayArrow } from 'react-icons/md';
import type { Call } from '@unpod/constants/types';

type PlayButtonProps = {
  item: Call;
};

const PlayButton = ({ item }: PlayButtonProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [loading, setLoading] = useState(false);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [isPlaying, setPlaying] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const onPlaySound = () => {
    if (fileUrl) {
      if (!audioRef.current) return;
      if (isPlaying) audioRef.current.pause();
      else audioRef.current.play();
      setPlaying(!isPlaying);
    } else {
      setLoading(true);
      getDataApi<{ url?: string }>(
        'media/pre-signed-url/',
        infoViewActionsContext,
        {
          url: item.output?.recording_url,
        },
      )
        .then((res) => {
          const url = res.data?.url;
          if (!url) {
            infoViewActionsContext.showError('Unable to load audio.');
            setLoading(false);
            return;
          }
          const audio = new Audio(url);
          audioRef.current = audio;
          setFileUrl(url);
          audio.play();
          audio.onended = () => {
            setPlaying(false);
          };
          setLoading(false);
          setPlaying(true);
        })
        .catch((response) => {
          infoViewActionsContext.showError(response.message);
          setLoading(false);
        });
    }
  };

  return isPlaying ? (
    <Tooltip title="Pause">
      <Button
        shape="circle"
        size="small"
        icon={<MdOutlinePause fontSize={18} />}
        onClick={(e) => {
          onPlaySound();
          e.stopPropagation();
        }}
        style={{ color: 'red' }} // Change color to indicate pause state
      />
    </Tooltip>
  ) : (
    <Tooltip title="Play">
      <Button
        shape="circle"
        size="small"
        icon={<MdOutlinePlayArrow fontSize={18} />}
        onClick={(e) => {
          onPlaySound();
          e.stopPropagation();
        }}
        loading={loading}
      />
    </Tooltip>
  );
};

export default PlayButton;
