import { Fragment } from 'react';
import SectionHeader from '../SectionHeader';
import { tasks } from '../data';
import { StyledAvatar, StyledDocumentsList } from '../index.styled';
import { MdCheck } from 'react-icons/md';
import AppList from '@unpod/components/common/AppList';
import TaskItem from '../TaskItem';

const UpcomingTasks = () => {
  const count = tasks.filter((task) => task.status === 'upcoming').length;
  return (
    <Fragment>
      <SectionHeader lable="Upcoming" count={count} />

      <StyledDocumentsList>
        <AppList
          data={tasks.filter((task) => task.status === 'upcoming')}
          renderItem={(item: any) => (
            <TaskItem
              item={item}
              avatar={
                <StyledAvatar
                  className="upcoming"
                  icon={<MdCheck size={18} />}
                  shape="square"
                  size={35}
                />
              }
            />
          )}
        />
      </StyledDocumentsList>
    </Fragment>
  );
};

export default UpcomingTasks;
