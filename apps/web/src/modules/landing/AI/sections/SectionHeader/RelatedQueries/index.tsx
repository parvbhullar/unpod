import React from 'react';
import { Divider, Typography } from 'antd';
import { MdSearch } from 'react-icons/md';
import {
  StyledContainer,
  StyledContent,
  StyledListItem,
  StyledSourceList,
} from './index.styled';

/*const queries = [
  'How much is the global life science software market expected to be worth by 2032?',
  'How much is the U.S. Contract Research Organization (CRO) services market worth?',
  'Who are the prominent players operating in the clinical trial investigative site network market?',
  'How much will the email marketing software market be worth by 2032?',
  'What is the estimated growth rate of the automotive domain controller market?',
];*/

const queries = [
  "What's the best way to learn a new language quickly?",
  'Can you recommend some sci-fi novels similar to "Dune"?',
  'What should I do if I lose my passport while traveling abroad?',
  'Latest news on global market trends.',
  'Tips for renovating a kitchen on a budget.',
];

const { Title } = Typography;

type QueryRef = {
  askQuery?: (payload: { content: string }) => void;
};

type RelatedQueriesProps = {
  queryRef: React.RefObject<QueryRef>;
};

const RelatedQueries: React.FC<RelatedQueriesProps> = ({ queryRef }) => {
  const onClick = (content: string) => {
    queryRef.current?.askQuery?.({ content });
  };

  return (
    <StyledContainer>
      <Title level={2} className="text-center">
        Queries
      </Title>

      <StyledSourceList as="ul">
        {queries.map((source, index) => (
          <StyledListItem key={index} onClick={() => onClick(source)}>
            <StyledContent>
              <MdSearch fontSize={20} /> {source}
            </StyledContent>

            {index < queries.length - 1 && <Divider style={{ margin: '0' }} />}
          </StyledListItem>
        ))}
      </StyledSourceList>
    </StyledContainer>
  );
};

export default RelatedQueries;
