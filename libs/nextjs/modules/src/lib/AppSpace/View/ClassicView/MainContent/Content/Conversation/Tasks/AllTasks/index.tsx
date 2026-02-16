import { Fragment } from 'react';
import CompletedTasks from '../CompletedTasks';
import UpcomingTasks from '../UpcomingTasks';
import FailedTasks from '../FailedTasks';

const AllTasks = () => {
  return (
    <Fragment>
      <UpcomingTasks />
      <CompletedTasks />
      <FailedTasks />
    </Fragment>
  );
};

export default AllTasks;
