import {getDataApi, useInfoViewActionsContext} from '@unpod/providers';
import {useRef, useState} from 'react';
import {Button, Tooltip} from 'antd';
import {MdOutlinePause, MdOutlinePlayArrow} from 'react-icons/md';

const PlayButton = ({item}: { item: any }) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [loading, setLoading] = useState(false);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [isPlaying, setPlaying] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const onPlaySound = () => {
    if (fileUrl) {
      if (isPlaying) {
        audioRef.current?.pause();
        setPlaying(false);
      } else {
        audioRef.current?.play();
        setPlaying(true);
      }
    } else {
      setLoading(true);
      getDataApi('media/pre-signed-url/', infoViewActionsContext, {
        url: item.output.recording_url,
      })
        .then((res: any) => {
          const url = res?.data?.url;
          if (!url) return;
          audioRef.current = new Audio(url);
          setFileUrl(url);
          audioRef.current?.play();
          if (audioRef.current) {
            audioRef.current.onended = () => {
              setPlaying(false);
            };
          }
          setPlaying(false);
          setLoading(false);
          setPlaying(true);
        })
        .catch((response: any) => {
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
        icon={<MdOutlinePause fontSize={18}/>}
        onClick={onPlaySound}
        style={{color: 'red'}} // Change color to indicate pause state
      />
    </Tooltip>
  ) : (
    <Tooltip title="Play">
      <Button
        shape="circle"
        size="small"
        icon={<MdOutlinePlayArrow fontSize={18}/>}
        onClick={onPlaySound}
        loading={loading}
      />
    </Tooltip>
  );
};

export default PlayButton;
