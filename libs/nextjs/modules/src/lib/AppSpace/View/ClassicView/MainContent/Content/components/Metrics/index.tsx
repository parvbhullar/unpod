import {Flex, Typography} from 'antd';
import styled from 'styled-components';
import AppGrid from '@unpod/components/common/AppGrid';
import AppLink from '@unpod/components/next/AppLink';
import {StyledAnalyticsCard, StyledCardTitle,} from '../../People/Overview/Summary/index.styled';

const {Text} = Typography;

const StyledLinkText = styled(Text)`
  color: ${({theme}) => theme.palette.primary};
  cursor: pointer;
  transition: color 0.3s ease;

  &:hover {
    color: ${({theme}) => theme.palette.primary};
  }
`;
const AppGridAny = AppGrid as any;

const Metrics = ({data}: { data: any[] }) => {
  return (
    <AppGridAny
      data={data}
      itemPadding={16}
      responsive={{
        xs: 1,
        sm: 2,
        md: 2,
        lg: 2,
        xl: 3,
        xxl: 3,
      }}
      hideNoDataMessage
      renderItem={(item: any) => (
        <StyledAnalyticsCard key={item.key}>
          <Flex vertical>
            <StyledCardTitle type="secondary">
              {item.label || 'N/A'}
            </StyledCardTitle>
            {item.link ? (
              <AppLink href={item.link}>
                <StyledLinkText strong>{item.value || 'N/A'}</StyledLinkText>
              </AppLink>
            ) : (
              <Text strong>{item.value || 'N/A'}</Text>
            )}
          </Flex>
        </StyledAnalyticsCard>
      )}
    />
  );
};

export default Metrics;
