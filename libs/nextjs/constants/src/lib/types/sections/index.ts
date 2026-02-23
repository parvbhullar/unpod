import type {ReactNode} from 'react';

export type SectionHeadingProps = {
  heading?: string;
  subHeading?: string;
  description?: string;
};

export type SectionListItem = {
  id: string | number;
  title?: string;
  description?: string;
  icon?: string;
};

export type SectionClientItem = {
  id: string | number;
  name?: string;
  logo?: string;
};

export type SectionFaqItem = {
  id: string | number;
  question: string;
  answer: ReactNode;
};

export type SectionImageInfoData = {
  heading: string;
  subHeading?: string;
  description?: string;
  items?: Array<{
    description: string;
  }>;
  image: {
    url: string;
    alt?: string;
  };
};

export type SectionMetricsItem = {
  id: string | number;
  icon?: string;
  title: string;
  description: string;
};
