export const duration = '12:34';
export const currentTime = '4:23';
export const progress = 35;

export const keyPoints = [
  {
    id: 1,
    title: 'Time tracking methodology discussed',
    meta: 'Recommended using standardized format for consistency',
  },
  {
    id: 2,
    title: 'Calculation formula provided',
    meta: 'Step-by-step breakdown of hour calculations',
  },
  {
    id: 3,
    title: 'Best practices reviewed',
    meta: 'Industry standards and recommendations shared',
  },
];

export const getParticipants = (activeConversation: any) => [
  {
    id: 1,
    name: activeConversation?.user?.full_name || 'User',
    role: 'Started the conversation',
    time: '5 days ago',
    avatar:
      activeConversation?.user?.full_name?.substring(0, 1).toUpperCase() || 'U',
    color: '#796CFF',
  },
  {
    id: 2,
    name: 'Assistant',
    role: 'Provided guidance and solutions',
    time: '',
    avatar: 'AI',
    color: '#67AA49',
  },
];

export const previousConversations = [
  {
    id: 1,
    title: 'No Title',
    preview: 'How can we assist you today?',
    time: '10 days ago',
    user: {
      id: 2,
      full_name: 'Parvinder Singh',
      email: 'parv@gmail.com',
      profile_color: '#796CFF',
    },
  },
  {
    id: 2,
    title: 'Understanding The Basics O...',
    preview: 'hi',
    time: '1 month ago',
    avatar: 'PS',
    user: {
      id: 2,
      full_name: 'Parvinder Singh',
      email: 'parv@gmail.com',
      profile_color: '#796CFF',
    },
  },
  {
    id: 3,
    title: 'No Title',
    preview: 'People who are willing to purchase.',
    time: '1 month ago',
    avatar: 'PS',
    user: {
      id: 2,
      full_name: 'Parvinder Singh',
      email: 'parv@gmail.com',
      profile_color: '#796CFF',
    },
  },
  {
    id: 4,
    title: 'No Title',
    preview: 'test',
    time: '1 month ago',
    avatar: 'PS',
    user: {
      id: 2,
      full_name: 'Parvinder Singh',
      email: 'parv@gmail.com',
      profile_color: '#796CFF',
    },
  },
];

export const getSummary = (activeConversation: any) =>
  activeConversation?.summary ||
  `
  # Current Tech Stack Challenges
   Using Exotel + WebSockets + Azure OpenAI for voice bot infrastructure
   Audio quality issues at 8kHz sampling rate from Exotel
   Cost concerns with Exotel at 30-40 paise per minute

  # Proposed Technical Solution
   Switch from WebSockets to WebRTC + LiveKit framework
   Two service options from Unpod: SIP dialer mode or full agent mode
   Platform features demonstrated with conversational flows
   Switch from WebSockets to WebRTC + LiveKit framework
   Two service options from Unpod: SIP dialer mode or full agent mode

`;

export const getOverviewData = (activeConversation: any) => ({
  participants: getParticipants(activeConversation),
  summary: getSummary(activeConversation),
  hasAudio: activeConversation.audio_url,
});
