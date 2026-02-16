import React from 'react';
import { StyledFeatureContentWrapper } from './index.styled';
import renderHTML from '@unpod/external-libs/react-render-html';
import { Typography } from 'antd';

const { Title } = Typography;

type FeaturesContentData = {
  title: string;
  description: string;
};

type FeaturesContentProps = {
  data: FeaturesContentData;
};

const FeaturesContent: React.FC<FeaturesContentProps> = ({ data }) => {
  return (
    <StyledFeatureContentWrapper>
      <Title level={5} type="secondary">
        {renderHTML(data.title)}
      </Title>

      <Typography.Paragraph type="secondary">
        {renderHTML(data.description)}
      </Typography.Paragraph>
    </StyledFeatureContentWrapper>
  );
};

export default React.memo(FeaturesContent);
