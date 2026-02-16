import React, { Fragment } from 'react';
import { enterpriseData } from '../../../@db/enterprise';

import SectionFaqs from '../../common/SectionFaqs';
import SectionClients from '../../common/SectionClients';
import SectionFeatures from '../../common/SectionFeatures';
import SectionUseCases from '../../common/SectionUseCases';
// const SectionServices = dynamic(() => import('../common/SectionServices'), {
//   ssr: false,
// });
import SectionHeader from './sections/SectionHeader';

const EnterpriseModule = () => {
  return (
    <Fragment>
      <SectionHeader />
      <SectionFeatures {...enterpriseData.features} />
      <SectionClients {...enterpriseData.clients} />
      {/*<SectionServices {...enterpriseData.services} />*/}
      <SectionUseCases {...enterpriseData.useCases} />
      <SectionFaqs {...enterpriseData.faqs} />
    </Fragment>
  );
};

export default EnterpriseModule;
