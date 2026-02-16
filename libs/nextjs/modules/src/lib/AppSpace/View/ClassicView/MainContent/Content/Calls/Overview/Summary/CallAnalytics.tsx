import { Flex, Typography } from 'antd';
import { StyledLabel } from './index.styled';

const { Paragraph } = Typography;

const CallAnalytics = ({ label, value }: { label: any; value: any }) => {
  const isString = typeof value === 'string';
  return (
    <Flex align="center" gap={30}>
      <StyledLabel strong>{label}</StyledLabel>
      {isString ? (
        <div dangerouslySetInnerHTML={{ __html: value }} />
      ) : (
        <Paragraph
          style={{ margin: 0 }}
          ellipsis={{
            rows: 2,
            expandable: false,
            tooltip: value,
          }}
        >
          {value || 'N/A'}
        </Paragraph>
      )}
    </Flex>
  );
};

export default CallAnalytics;
