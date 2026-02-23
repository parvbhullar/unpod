import React from 'react';
import {ConferencingFooter} from './ConferencingFooter';
// import { StreamingFooter } from './StreamingFooter';
import {isStreamingKit} from '../../common/utils';

export const Footer = () => {
  return isStreamingKit() ? (
    /*<StreamingFooter />*/ <div/>
  ) : (
    <ConferencingFooter/>
  );
};

export default Footer;
