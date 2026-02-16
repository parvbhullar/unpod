import React from 'react';
import {
  StyledFeatureCardWrapper,
  StyledFeatureImageContent,
  StyledFeatureImageWrapper,
} from './index.styled';
import renderHTML from '@unpod/external-libs/react-render-html';
import { Typography } from 'antd';
import AppImage from '@unpod/components/next/AppImage';

type FeatureItem = {
  image: string;
  title: string;
  description?: string;
};

type FeatureCardProps = {
  data: FeatureItem;
};

const FeatureCard: React.FC<FeatureCardProps> = ({ data }) => {
  return (
    <StyledFeatureCardWrapper>
      <StyledFeatureImageWrapper>
        <AppImage src={data.image} alt="security" width={280} height={248} />
      </StyledFeatureImageWrapper>

      <StyledFeatureImageContent className="feature-content">
        <Typography.Title level={5} type="secondary">
          {renderHTML(data.title)}
        </Typography.Title>
        {data.description ? (
          <Typography.Paragraph type="secondary">
            {renderHTML(data.description)}
          </Typography.Paragraph>
        ) : (
          ''
        )}
      </StyledFeatureImageContent>
    </StyledFeatureCardWrapper>
  );
};

export default React.memo(FeatureCard);
