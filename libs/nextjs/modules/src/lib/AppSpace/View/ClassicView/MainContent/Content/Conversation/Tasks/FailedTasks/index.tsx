import { Fragment } from 'react';
import { StyledAvatar, StyledDocumentsList } from '../index.styled';
import { RxCross2 } from 'react-icons/rx';
import { tasks } from '../data';
import SectionHeader from '../SectionHeader';
import AppList from '@unpod/components/common/AppList';
import TaskItem from '../TaskItem';

const FailedTasks = () => {
  const count = tasks.filter((task) => task.status === 'failed').length;

  return (
    <Fragment>
      <SectionHeader lable="Failed" count={count} />

      <StyledDocumentsList>
        <AppList
          data={tasks.filter((task) => task.status === 'failed')}
          renderItem={(item: any) => (
            <TaskItem
              item={item}
              avatar={
                <StyledAvatar
                  className="failed"
                  icon={<RxCross2 size={18} />}
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

export default FailedTasks;
