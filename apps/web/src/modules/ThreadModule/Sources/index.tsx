import React from 'react';
import { Space, Typography } from 'antd';
import { MdAlbum, MdGridView } from 'react-icons/md';
import { StyledContainer, StyledSourceList } from './index.styled';
import SourceCard from './SourceCard';

const { Title, Text } = Typography;

const sources = [
  {
    query: 'Students data for colleges',
    icon: <MdAlbum fontSize={20} />,
    title: 'Source 1',
  },
  {
    query: 'PG colleges/institutions needs professional data.',
    icon: <MdAlbum fontSize={20} />,
    title: 'Source 2',
  },
  {
    query: 'Agency needs data of Business/influencers data.',
    icon: <MdAlbum fontSize={20} />,
    title: 'Source 3',
  },
  {
    query: 'Cost comparisons of softwares for purchasing',
    icon: <MdAlbum fontSize={20} />,
    title: 'Source 4',
  },
];

const Sources = () => {
  return (
    <StyledContainer>
      <Title level={3}>
        <Space>
          <MdGridView fontSize={20} />
          <Text>Sources</Text>
        </Space>
      </Title>
      <StyledSourceList>
        {sources.map((source, index) => (
          <SourceCard key={index} source={source} />
        ))}
      </StyledSourceList>
    </StyledContainer>
  );
};

export default Sources;
