import {
  StyledAvatar,
  StyledDateHeader,
  StyledDateSection,
} from './index.styled';
import ListItems from '../ListItems';
import { keyPoints } from '../data';
import { MdCheck } from 'react-icons/md';

const KeyPoints = () => {
  return (
    <StyledDateSection>
      <StyledDateHeader strong type="secondary">
        KEY POINTS
      </StyledDateHeader>
      {keyPoints.map((point) => (
        <ListItems
          key={point.id}
          title={point.title}
          description={point.meta}
          avatar={
            <StyledAvatar
              icon={<MdCheck size={18} />}
              shape="square"
              size={36}
            />
          }
        />
      ))}
    </StyledDateSection>
  );
};

export default KeyPoints;
