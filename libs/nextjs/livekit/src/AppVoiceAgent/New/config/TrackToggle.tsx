import React, { ReactNode } from 'react';
import { useTrackToggle, UseTrackToggleProps } from '@livekit/components-react';
import Button from '../../components/Button';
import { FiMic, FiMicOff } from 'react-icons/fi';
import { Track } from 'livekit-client';

interface TrackToggleProps extends UseTrackToggleProps<Track.Source> {
  children?: ReactNode;
}

export const TrackToggle: React.FC<TrackToggleProps> = (props) => {
    const { buttonProps, enabled } = useTrackToggle(props);
    const [isClient, setIsClient] = React.useState(false);
    React.useEffect(() => {
      setIsClient(true);
    }, []);

    return (
      isClient && (
        <Button
          type="primary"
          shape="circle"
          icon={enabled ? <FiMic /> : <FiMicOff />} onClick={buttonProps.onClick}>
          {props.children}
        </Button>
      )
    );
  }
;