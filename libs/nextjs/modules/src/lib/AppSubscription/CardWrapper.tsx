import { StyledCard } from './index.styled';
import { Typography } from 'antd';

const { Title, Paragraph, Text } = Typography;

const CardWrapper = ({
  title,
  subtitle,
  desc,
  children,
  ...restProps
}: {
  title?: any;
  subtitle?: any;
  desc?: any;
  children?: any;
  [key: string]: any;
}) => {
  return (
    <StyledCard
      title={
        title && (
          <div>
            <div className="title-row">
              <Title level={5} style={{ margin: 0 }}>
                {title}
              </Title>
              <Text style={{ fontWeight: 500, fontSize: 14 }}>{subtitle}</Text>
            </div>
            {desc && <Paragraph type="secondary">{desc}</Paragraph>}
          </div>
        )
      }
      {...restProps}
    >
      {children}
    </StyledCard>
  );
};

export default CardWrapper;
