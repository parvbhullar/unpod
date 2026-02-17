import {RiRobot2Line} from 'react-icons/ri';
import {IoDocumentsOutline} from 'react-icons/io5';

export const profiles = {
  'unpod.ai': [
    {
      name: 'dashboard.createSpaceTitle',
      description: 'dashboard.CreateSpaceDescription',
      profile_pic: '/images/unpod-icon.png',
      icon: <IoDocumentsOutline fontSize={36} />,
      url: '/spaces',
    },
    {
      name: 'dashboard.CreateAIIdentityTitle',
      description: 'dashboard.CreateAIIdentityDescription',
      profile_pic: '/images/unpod-icon.png',
      icon: <RiRobot2Line fontSize={36} />,
      url: '/ai-studio',
    },
  ],
};
