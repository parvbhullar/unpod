import { Divider, Space, Typography } from 'antd';
import { MdAdd, MdOutlineLocalLibrary } from 'react-icons/md';
import {
  StyledContainer,
  StyledContent,
  StyledListItem,
  StyledSourceList,
} from './index.styled';
import { useIntl } from 'react-intl';

const { Title, Text } = Typography;

const queries = [
  'queries.q1',
  'queries.q2',
  'queries.q3',
  'queries.q4',
  'queries.q5',
];

const RelatedQueries = () => {
  const { formatMessage } = useIntl();

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
              <MdAdd fontSize={20} /> {formatMessage({ id: source })}
            </StyledContent>

            <Divider style={{ margin: '0' }} />
          </StyledListItem>
        ))}
      </StyledSourceList>
    </StyledContainer>
  );
};

export default RelatedQueries;
