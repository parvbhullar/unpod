import { Space, Typography } from 'antd';
import { StyledParagraph, StyledRoot } from './index.styled';
import type { ReactNode } from 'react';

const { Text } = Typography;

type Source = {
  query?: string;
  icon?: ReactNode;
  title?: string;
};

type SourceCardProps = {
  source: Source;
};

const SourceCard = ({ source }: SourceCardProps) => {
  return (
    <StyledRoot>
      <StyledParagraph>{source.query}</StyledParagraph>
      <Space>
        {source.icon}
        <Text>{source.title}</Text>
      </Space>
    </StyledRoot>
  );
};

export default SourceCard;
