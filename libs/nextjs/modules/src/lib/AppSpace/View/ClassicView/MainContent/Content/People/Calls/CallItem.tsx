import { RenderDescription } from './RenderDescription';
import { StyledAvatar } from './index.styled';
import PlayButton from './PlayButton';
import { Typography } from 'antd';
import ListItems from '../../Conversation/Overview/ListItems';

import { MdCheck } from 'react-icons/md';
import { RxCross2 } from 'react-icons/rx';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';
import type { Call } from '@unpod/constants/types';

type CallItemProps = {
  data: Call;
  onCallClick: (data: Call) => void;
};

const getStatusIcon = (status: string | undefined, mobileScreen: boolean) => {
  if (status === 'failed') return <RxCross2 size={mobileScreen ? 16 : 20} />;
  if (status === 'hold') return <RxCross2 size={mobileScreen ? 16 : 20} />;
  return <MdCheck size={mobileScreen ? 16 : 20} />;
};
const { Text } = Typography;
const CallItem = ({ data, onCallClick }: CallItemProps) => {
  const mobileScreen = useMediaQuery(MobileWidthQuery);

  return (
    <ListItems
      onClick={() => onCallClick(data)}
      title={
        <Text
          strong
          className="text-capitalize"
          style={{ fontSize: 15, color: '#262626' }}
        >
          {data.task?.objective === 'call'
            ? `${data.task?.objective} to ${data?.input?.name}`
            : data.task?.objective}
        </Text>
      }
      description={<RenderDescription item={data} />}
      avatar={
        <StyledAvatar
          className={
            data.status === 'completed'
              ? 'success'
              : data.status === 'failed'
                ? 'error'
                : ''
          }
          icon={getStatusIcon(data.status, mobileScreen)}
          shape="square"
          size={mobileScreen ? 35 : 40}
        />
      }
      $radius={12}
      recordingButton={
        data.status === 'completed' &&
        (data.output?.recording_url ? <PlayButton item={data} /> : null)
      }
    />
  );
};

export default CallItem;
