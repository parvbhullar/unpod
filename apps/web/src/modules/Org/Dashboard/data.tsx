import { MdOutlinePhone } from 'react-icons/md';
import { RiRobot2Line } from 'react-icons/ri';
import { IoDocumentsOutline } from 'react-icons/io5';

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
    {
      name: 'dashboard.SetupTelephonyTitle',
      description: 'dashboard.SetupTelephonyDescription',
      profile_pic: '/images/unpod-icon.png',
      icon: <MdOutlinePhone fontSize={36} />,
      url: '/bridges',
    },
  ],
  'unpod.dev': [
    {
      name: 'dashboard.SetupTelephonyTitle',
      description: 'dashboard.SetupTelephonyDescription',
      profile_pic: '/images/unpod-icon.png',
      icon: <MdOutlinePhone fontSize={36} />,
      url: '/bridges',
    },
    {
      name: 'dashboard.SetupAgentName',
      description: 'dashboard.SetupAgentDescription',
      profile_pic: '/images/unpod-icon.png',
      icon: <RiRobot2Line fontSize={36} />,
      url: '/ai-studio',
    },
  ],
};

// {
//   name: 'Spotify',
//   description:
//     'Spotify is a digital music service that gives you access to millions of songs.',
//   profile_pic: '/images/spotify-icon.png',
//   icon: <RiUser3Line fontSize={36} />,
//   url: 'https://spotify.com',
// },
// {
//   name: 'Apple Podcasts',
//   description: 'Apple Podcasts is a podcast app for iOS devices.',
//   profile_pic: '/images/apple-podcasts-icon.png',
//   icon: <MdOutlinePhone fontSize={36} />,
//   url: 'https://podcasts.apple.com',
// },
