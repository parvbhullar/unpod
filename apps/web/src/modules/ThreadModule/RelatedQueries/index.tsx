import React from 'react';
import { Divider, Space, Typography } from 'antd';
import { MdAdd, MdOutlineLocalLibrary } from 'react-icons/md';
import {
  StyledContainer,
  StyledContent,
  StyledListItem,
  StyledSourceList,
} from './index.styled';

const { Title, Text } = Typography;

const queries = [
  'What are the top companies currently using SaaS HR tools',
  'How can I find contact information for HR Decision -makers at large corporations',
  'Are there any databases that provide email lists for HR professionals',
  'What are the best practices for reaching out to HR prospects',
  'Can I get a list of companies that recently implemented HR SaaS solutions',
];

const RelatedQueries = () => {
  return (
    <StyledContainer>
      <Title level={3}>
        <Space>
          <MdOutlineLocalLibrary fontSize={20} />
          <Text>Followup</Text>
        </Space>
      </Title>
      <StyledSourceList as="ul">
        {queries.map((source, index) => (
          <StyledListItem key={index}>
            {index === 0 && <Divider style={{ margin: '0' }} />}

            <StyledContent>
              <MdAdd fontSize={20} /> {source}
            </StyledContent>

            <Divider style={{ margin: '0' }} />
          </StyledListItem>
        ))}
      </StyledSourceList>
    </StyledContainer>
  );
};

export default RelatedQueries;
