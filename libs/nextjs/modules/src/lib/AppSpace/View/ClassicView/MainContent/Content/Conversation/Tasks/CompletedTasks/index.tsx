import { Fragment } from 'react';
import SectionHeader from '../SectionHeader';
import { StyledAvatar, StyledDocumentsList } from '../index.styled';
import { MdCheck } from 'react-icons/md';
import { tasks } from '../data';
import AppList from '@unpod/components/common/AppList';
import TaskItem from '../TaskItem';

const CompletedTasks = () => {
  const count = tasks.filter((task) => task.status === 'completed').length;

  return (
    <Fragment>
      <SectionHeader lable="Completed" count={count} />

      <StyledDocumentsList>
        <AppList
          data={tasks.filter((task) => task.status === 'completed')}
          renderItem={(item: any) => (
            <TaskItem
              item={item}
              avatar={
                <StyledAvatar
                  className="completed"
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

export default CompletedTasks;
