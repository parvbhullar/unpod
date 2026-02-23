import React, {ReactNode} from 'react';
import {useTrackToggle, type UseTrackToggleProps,} from '@livekit/components-react';
import Button from '../../components/Button';
import {FiMic, FiMicOff} from 'react-icons/fi';

type TrackToggleProps = UseTrackToggleProps<any> & {
  children?: ReactNode;
};

export const TrackToggle: React.FC<TrackToggleProps> = (props) => {
  const {buttonProps, enabled} = useTrackToggle(props);
  const [isClient, setIsClient] = React.useState(false);
  React.useEffect(() => {
    setIsClient(true);
  }, []);

  return (
    isClient && (
      <Button
        variant="primary"
        shape="circle"
        icon={enabled ? <FiMic/> : <FiMicOff/>}
        onClick={() => buttonProps.onClick?.(null as any)}
      >
        {props.children}
      </Button>
    )
  );
};
