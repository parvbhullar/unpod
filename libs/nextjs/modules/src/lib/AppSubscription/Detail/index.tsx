import { Alert, Button, Typography } from 'antd';
import {
  StyledButtonWrapper,
  StyledSection,
  StyledSectionLeft,
} from '../index.styled';
import UsageStatsCards from './UsageStatsCards';
import ActivePlanSummary from './ActivePlanSummary';
import MonthlyUsageReport from './MonthlyUsageReport';
import PaymentStatements from './PaymentStatements';
import { FaArrowRight, FaMoneyCheckDollar } from 'react-icons/fa6';
import { MdCreditCard } from 'react-icons/md';
import { RiPriceTag3Line } from 'react-icons/ri';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';
import { useIntl } from 'react-intl';

const { Title, Paragraph } = Typography;
const AlertAny = Alert as any;

export const BillingDetail = ({
  subscription,
  onChangePlan,
}: {
  subscription: any;
  onChangePlan: () => void;
}) => {
  const mobileScreen = useMediaQuery(MobileWidthQuery);
  const { formatMessage } = useIntl();

  return (
    <>
      <StyledSection>
        <StyledSectionLeft>
          <Title level={3} style={{ margin: 0 }}>
            {formatMessage({ id: 'billing.pageTitle' })}
          </Title>
          <Paragraph
            type={'secondary'}
            style={{ margin: 0 }}
            ellipsis={{
              rows: 1,
              expandable: mobileScreen && true,
              symbol: formatMessage({ id: 'common.readMore' }),
            }}
          >
            {formatMessage({ id: 'billing.description' })}
          </Paragraph>
        </StyledSectionLeft>
        <StyledButtonWrapper>
          {subscription?.has_subscription ? (
            <Button
              type="primary"
              iconPlacement={'end'}
              icon={
                mobileScreen ? (
                  <FaMoneyCheckDollar size={30} />
                ) : (
                  <FaArrowRight size={14} />
                )
              }
              onClick={onChangePlan}
            >
              {!mobileScreen && formatMessage({ id: 'billing.upgrade' })}
            </Button>
          ) : (
            <Button
              type="primary"
              iconPlacement={'end'}
              icon={
                mobileScreen ? (
                  <MdCreditCard size={30} />
                ) : (
                  <FaArrowRight size={14} />
                )
              }
              onClick={onChangePlan}
            >
              {!mobileScreen &&
                formatMessage({
                  id: 'billing.choosePlan',
                })}
            </Button>
          )}
        </StyledButtonWrapper>
      </StyledSection>
      {!subscription?.has_subscription && (
        <AlertAny
          type="warning"
          showIcon
          message={formatMessage({ id: 'billing.alertMessage' })}
          action={
            <Button
              size="small"
              type="primary"
              ghost
              shape={mobileScreen ? 'circle' : 'default'}
              onClick={onChangePlan}
              iconPlacement={'end'}
              icon={mobileScreen && <RiPriceTag3Line size={18} />}
            >
              {!mobileScreen && formatMessage({ id: 'billing.viewPlans' })}
            </Button>
          }
        />
      )}
      <ActivePlanSummary subscription={subscription} />
      {subscription?.has_subscription && (
        <UsageStatsCards subscription={subscription} />
      )}
      <MonthlyUsageReport subscription={subscription} />
      <PaymentStatements />
    </>
  );
};

export default BillingDetail;
