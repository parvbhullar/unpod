import {Space, Typography} from 'antd';
import {type ReactNode} from 'react';
import {StyledParagraph, StyledRoot} from './index.styled';
import {useIntl} from 'react-intl';

const {Text} = Typography;

type SourceCardProps = {
  source: { query: string; title: string; icon?: ReactNode };
};

const SourceCard = ({source}: SourceCardProps) => {
  const {formatMessage} = useIntl();
  return (
    <StyledRoot>
      <StyledParagraph>{formatMessage({id: source.query})}</StyledParagraph>
      <Space>
        {source.icon}
        <Text>{formatMessage({id: source.title})}</Text>
      </Space>
    </StyledRoot>
  );
};

export default SourceCard;
