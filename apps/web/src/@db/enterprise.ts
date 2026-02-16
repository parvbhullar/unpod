const features = [
  {
    id: 1,
    icon: 'database',
    title: 'Connect with datasources',
    description:
      'Connect with different public and private data sources, instantly.',
  },
  {
    id: 2,
    icon: 'import',
    title: 'Import Data files',
    description:
      'We supports import of every type of data files such as spreadsheets, documents, webpages.',
  },
  {
    id: 3,
    icon: 'instantly',
    title: 'Read & Extract Data with AI',
    description:
      'Pull the key insights and metrics from documents and data sources, automatically.',
  },
  {
    id: 4,
    icon: 'document-search',
    title: 'Intelligent Search & Insights',
    description:
      'We help you reason over every document, datasources, generate usable insight to get answers for decision making.',
  },
  {
    id: 5,
    icon: 'decision',
    title: 'Decision Markers',
    description:
      'Create custom decision markers based on your preferences for Instantly flag issues with your transactions or documents and responses.',
  },
  {
    id: 6,
    icon: 'workflow',
    title: 'Create your workflows',
    description:
      'Unpod allows you to create your workflows to generate insights, decision markers, reports and memos.',
  },
];

const useCases = [
  {
    id: 1,
    icon: 'real-estate',
    title: 'Market Size & forecasting',
    description:
      'Estimating market size and forecasting growth potential using historical data, economic indicators, and market trends, assisting businesses in market entry and expansion decisions.',
  },
  {
    id: 2,
    icon: 'private-equity',
    title: 'Financial Analysis',
    description:
      'Automating the analysis of financial data, including revenue, expenses, and cash flow, to generate accurate forecasts, identify trends, and support budgeting and financial planning.',
  },
  {
    id: 3,
    icon: 'tax-credit',
    title: 'Tax Credit Diligence',
    description:
      'Automate diligence for tax credit transfers and audits. Find overlooked risks, verify 100% of invoices & reports.',
  },
  {
    id: 4,
    icon: 'notices-orders',
    title: 'Regulatory Notices & Orders',
    description:
      'Prepare Responses to notices & orders from regulatory bodies like GSTN, NIC, IT and many more.',
  },
];

export const enterpriseData = {
  sectionHeader: {
    title: 'Enterprise',
    slogan: 'Features that make your website better',
    isWhite: true,
  },
  useCases: {
    heading: 'Industry wise use-cases',
    // subHeading: 'Features that make your website better',
    items: useCases,
    tabs: [
      {
        id: 1,
        title: 'EdTech',
        items: useCases,
      },
      {
        id: 2,
        title: 'RegTech',
        items: useCases,
      },
      {
        id: 3,
        title: 'FinTech',
        items: useCases,
      },
    ],
  },
  services: {
    heading: 'Our Services',
    // subHeading: 'We provide the following services',
    items: [
      {
        id: 1,
        icon: 'assignment',
        title: 'Co-lending and direct assignment',
        description:
          'Boost Co-lending across institutions via strong technology solutions and enhanced credit assessment to expand credit access.',
      },
      {
        id: 2,
        icon: 'security',
        title: 'Securitization and structured finance',
        description:
          'Effective selection, credit assessment and management of securitized pools backed with cutting edge analytics.',
      },
      {
        id: 3,
        icon: 'strategic',
        title: 'BC lending at scale',
        description:
          'Our strategic BC Partnerships help unlock fresh opportunities, strengthened by our LOS, LMS and Middleware solutions.',
      },
    ],
  },
  features: {
    heading: 'Features',
    subHeading:
      'Features will help you to execute research and analysis task fasters.',
    items: features,
  },
  clients: {
    heading: 'Trusted by reputed organisations',
    items: [
      {
        id: 1,
        name: 'Chegg',
        logo: '/images/clients-logos/chegg_logo.png',
      },
      {
        id: 2,
        name: 'Brainly',
        logo: '/images/clients-logos/brainly.in-logo.png',
      },
      {
        id: 3,
        name: 'Cloudbird',
        logo: '/images/clients-logos/cloudbirdventures_logo.jpeg',
      },
      /*{
        id: 4,
        name: 'Chegg',
        logo: '/images/clients-logos/chegg_logo.png',
      },
      {
        id: 5,
        name: 'Brainly',
        logo: '/images/clients-logos/brainly.in-logo.png',
      },
      {
        id: 6,
        name: 'Cloudbird',
        logo: '/images/clients-logos/cloudbirdventures_logo.jpeg',
      },*/
    ],
  },
  faqs: {
    heading: 'Frequently Asked Questions',
    // subHeading: 'Can’t find your question? Email us at info@unpod.ai',
    // description: 'Can’t find your question? Email us at info@unpod.ai.',
    items: [
      {
        id: 1,
        question: 'Is my data secure on Unpod’s platform?',
        answer:
          'Yes. All data is encrypted at rest and in transit. We have zero training and zero data retention policies with leading model providers.',
      },
      {
        id: 2,
        question: "Does Unpod train it's models on my data?",
        answer:
          'No. We do not train or fine-tune any models on your data. If we do fine-tune models as part of an engagement with you, only you and your team will have access.',
      },
      {
        id: 3,
        question: 'Do you support Excel / spreadsheets?',
        answer:
          'Yes! We are able to ingest, produce, and export spreadsheets as part of any workflows you configure on our platform.',
      },
      /*{
        id: 4,
        question: 'I heard LLMs are bad at math. How do you approach this?',
        answer:
          "We don't use LLMs to do math. Math is delegated to a separate, deterministic function. We show our work for everything.",
      },
      {
        id: 5,
        question: 'How do you measure accuracy?',
        answer:
          'We have internal benchmarks for a range of standard use cases including accurate fact extraction from various document formats, accurate context retrieval for common queries, and reasoning over spreadsheets which we plan on sharing in a future blog post.',
      },*/
      {
        id: 6,
        question: 'Will this work for my use case?',
        answer:
          'If your use case involves extracting standardized data, creating memos from a collection of source material, auditing figures across thousands of documents, building a knowledge base, or just chatting with PDFs, there is a good chance our product will be useful for you and your team. Contact us to learn more.',
      },
    ],
  },
};
