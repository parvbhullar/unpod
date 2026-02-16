const features = [
  {
    id: 1,
    icon: 'database',
    title: 'Collaborate on datasources',
    description:
      'Collaborate on different public and private data sources, enrich and share to generate insights.',
  },
  {
    id: 2,
    icon: 'document-search',
    title: 'Intelligent Search & Insights',
    description:
      'We help you reason over every document, datasources, generate usable insight to get answers for decision making.',
  },
  {
    id: 3,
    icon: 'workflow',
    title: 'Generate Reports',
    description:
      'Create custom insight reports based on different datasources and workflows. ',
  },
];

export const landing = {
  header: {
    heading: 'Empathetic AI Human-Like Conversation',
    subHeading: `It seamlessly connects to your calls, whatsapp, emails. It understands context, remove clutter, takes action, and keep tabs on everything.`,
  },
  howToWork: {
    heading: 'How unpod works',
    subHeading:
      'Unpod is a knowledge sharing platform for startups, teams and projects. Anyone can join the platform and start building publicly, where they can record their work sessions, meetings and podcasts about different things and topics.',
    items: [
      {
        image: '/images/signup.png',
        title: 'Register on platform to share and spin new ideas.',
      },
      {
        image: '/images/ideas.png',
        title:
          'You can record podcasts, stream live with your team while building your dream.',
      },
      {
        image: '/images/collaborate.png',
        title: 'Collaborate with likeminded people & grow your knowledge!',
      },
    ],
  },
  bestFeatures: {
    heading: 'Features',
    subHeading:
      'Features will help you to execute research and analysis task fasters.',
    items: features,
  },
  features: {
    heading: 'Features',
    subHeading:
      'Unpod.dev is a Low-Code LLM platform designed to automate complex and mundane tasks for organisations. We provide in-house AI assistants (Pilots) to efficiently handle routine tasks at a faster pace, along with support for both open and closed LLM models such as GPT4, Mixtral, and LLAMA.',
    featuresContent: [
      {
        id: 1,
        menuId: 'feature-1',
        image: '/images/landing/screen-mockup.png',
      },
      {
        id: 2,
        menuId: 'feature-2',
        image: '/images/landing/screen-mockup-1.png',
      },
      {
        id: 3,
        menuId: 'feature-3',
        image: '/images/landing/screen-mockup-2.png',
      },
      {
        id: 4,
        menuId: 'feature-4',
        image: '/images/landing/screen-mockup-3.png',
      },
      {
        id: 5,
        menuId: 'feature-5',
        image: '/images/landing/screen-mockup-4.png',
      },
      /*{
        id: 6,
        menuId: 'feature-6',
        image: '/images/landing/screen-mockup-5.png',
      },*/
    ],
    featuresPanel: [
      {
        id: 1,
        image: '/images/landing/features/team-collaboration.svg',
        title: 'Team Collaboration',
        description:
          'Onboard your team to complete mundane task faster using LLM pilots.',
      },
      {
        id: 2,
        image: '/images/landing/features/integrations.svg',
        title: 'Integrations',
        description:
          'Realtime connectivity with your data, documents and many more.',
      },
      {
        id: 3,
        image: '/images/landing/features/open-source.svg',
        title: 'Open-source Framework',
        description:
          'Open-source Framework to build LLM pilots on top of your tabular data, docs, emails, images.',
      },
      {
        id: 4,
        image: '/images/landing/features/pilots.svg',
        title: 'Pilots',
        description: 'Smart LLM agents to get things done.',
      },
      {
        id: 5,
        image: '/images/landing/features/models.svg',
        title: 'Models',
        description: 'Public and private models customised for your use case.',
      },
      /*{
        id: 6,
        image: '/images/landing/features/llm-cloud.svg',
        title: 'LLM Cloud',
        description:
          'End-to-End LLMops, GPUs and storage for LLM Pilots in your region.',
      },*/
    ],
  },
  connectors: {
    heading: 'Works on all platforms, no meeting bots',
    subHeading:
      "Granola transcribes your Mac's audio directly, with no meeting bots joining your call",
    items: [
      {
        id: 1,
        name: 'Email',
        logo: '/images/app-logos/gmail.png',
      },
      {
        id: 2,
        name: 'Whatsapp',
        logo: '/images/app-logos/whatsapp.png',
      },
      {
        id: 3,
        name: 'Slack',
        logo: '/images/app-logos/slack.png',
      },
      {
        id: 4,
        name: 'Discord',
        logo: '/images/app-logos/discord.png',
      },
      {
        id: 5,
        name: 'Webpages',
        logo: '/images/app-logos/webpages.png',
      },
      {
        id: 6,
        name: 'Documents',
        logo: '/images/app-logos/documents.png',
      },
    ],
  },
  privacy: {
    heading:
      'We value your privacy and do not use your personal data to train NotebookLM.',
    subHeading: 'Get notes in the exact format your team needs.',
    /*description:
      'NotebookLM does not use your personal data, including your source uploads, queries, and the responses from the model for training.',*/
    image: {
      // url: '/images/privacy-tornado.png',
      url: '/images/developer.svg',
      alt: 'Privacy',
    },
    items: [
      {
        id: 1,
        title: 'End-to-End Encryption',
        description:
          'All your data is encrypted end-to-end. Only you can access your data.',
      },
      {
        id: 2,
        title: 'GDPR Compliant',
        description:
          'We are GDPR compliant. We do not store any personal data.',
      },
      {
        id: 3,
        title: 'No Ads',
        description:
          'We do not show any ads. We do not sell your data to any third party.',
      },
    ],
  },
};
