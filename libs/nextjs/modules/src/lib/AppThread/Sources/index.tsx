import { Space, Typography } from 'antd';
import { MdAlbum, MdGridView } from 'react-icons/md';
import { StyledContainer, StyledSourceList } from './index.styled';
import SourceCard from './SourceCard';

const { Title, Text } = Typography;

const sources = [
  {
    query: 'sources.query1',
    icon: <MdAlbum fontSize={20} />,
    title: 'sources.title1',
  },
  {
    query: 'sources.query2',
    icon: <MdAlbum fontSize={20} />,
    title: 'sources.title2',
  },
  {
    query: 'sources.query3',
    icon: <MdAlbum fontSize={20} />,
    title: 'sources.title3',
  },
  {
    query: 'sources.query4',
    icon: <MdAlbum fontSize={20} />,
    title: 'sources.title4',
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
