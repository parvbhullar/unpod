import { Fragment } from 'react';
import { Button, Space, Typography } from 'antd';
import { MdCheck, MdClose } from 'react-icons/md';
import AppLink from '@unpod/components/next/AppLink';
import clsx from 'clsx';
import { getAmountWithCurrency } from '@unpod/helpers/CurrencyHelper';
import { useAuthContext } from '@unpod/providers';
import {
  StyledBadge,
  StyledButtonContainer,
  StyledFeatureItem,
  StyledIdealFor,
  StyledListContainer,
  StyledRow,
} from './index.styled';

import CardWrapper from '../../../../CardWrapper';
import { useIntl } from 'react-intl';

const { Title, Paragraph, Text } = Typography;

type PlanCardProps = {
  plan: any;
  loading?: boolean;
  onActivatePlan?: (plan: any) => void;
  onContactPlan?: (plan: any) => void;
  onCancelSubscription?: (plan: any) => void;
};

const PlanCard = ({
  plan,
  loading,
  onActivatePlan,
  onContactPlan,
  onCancelSubscription,
}: PlanCardProps) => {
  const { formatMessage } = useIntl();
  const { currency, subscription } = useAuthContext();

  const subscriptionId = (
    subscription as { subscription?: { id?: string } } | null
  )?.subscription?.id;

  const onActivateClick = () => {
    if (plan.id !== subscriptionId) {
      onActivatePlan?.(plan);
    }
  };

  // Determine badge variant and text
  const getBadgeInfo = () => {
    if (plan.is_popular) {
      return { variant: 'popular', text: `⭐ ${plan.tagline}` };
    }
    if (plan.is_default) {
      return { variant: 'default', text: plan.tagline };
    }
    if (plan.tagline) {
      return { variant: 'standard', text: plan.tagline };
    }
    return null;
  };

  const badgeInfo = getBadgeInfo();

  return (
    <CardWrapper
      title={plan.title}
      subtitle={plan.subtitle || ''}
      desc={plan.description}
      className={clsx({
        active: plan.id === subscriptionId,
      })}
    >
      {badgeInfo && (
        <StyledBadge $variant={badgeInfo.variant}>
          <span>{badgeInfo.text}</span>
        </StyledBadge>
      )}

      {plan.id === subscriptionId && plan.price > 0 && (
        <AppLink href="/wallet" passHref>
          Add Credits
        </AppLink>
      )}

      <StyledRow>
        {plan.type === 'contact' ? (
          <Title level={3}>Custom</Title>
        ) : (
          <div>
            {plan.discount > 0 ? (
              <Fragment>
                <div className="strike">{`${getAmountWithCurrency(plan.price, currency)} / month`}</div>
                <Title
                  level={3}
                >{`${getAmountWithCurrency(plan.final_price, currency)} / month`}</Title>
                {/*<div>
                  {`You save ${getAmountWithCurrency(plan.discount, currency)}`}
                </div>*/}
              </Fragment>
            ) : (
              <Title
                level={3}
              >{`${getAmountWithCurrency(plan.final_price, currency)} / month`}</Title>
            )}
          </div>
        )}
      </StyledRow>

      <StyledListContainer>
        {plan.modules.map((feature: any, index: number) => (
          <StyledFeatureItem key={index}>
            {feature?.included_in_sub ? (
              <MdCheck style={{ color: 'green' }} fontSize={18} />
            ) : (
              <MdClose style={{ color: 'red' }} fontSize={18} />
            )}
            <Typography>
              <Space>
                <Text strong>{feature.display_name}</Text>
                {/*{feature.quantity > 0 && <Text>{feature.quantity}</Text>}*/}
              </Space>
              <Paragraph
                type="secondary"
                style={{ fontSize: 12, marginBottom: 0 }}
              >
                {feature.description}
              </Paragraph>
            </Typography>
          </StyledFeatureItem>
        ))}
      </StyledListContainer>

      {plan.help_text && <StyledIdealFor>{plan.help_text}</StyledIdealFor>}

      <StyledButtonContainer $isHelpText={!!plan.help_text}>
        {plan.type === 'contact' ? (
          <Button
            type="primary"
            onClick={() => onContactPlan?.(plan)}
            block
            ghost
            disabled={loading}
          >
            Contact Us
          </Button>
        ) : (
          <>
            {plan.id === subscriptionId ? (
              <Button type="primary" ghost block>
                <MdCheck style={{ color: 'green' }} fontSize={18} />
                Activated Plan
              </Button>
            ) : (
              <Button
                type="primary"
                onClick={onActivateClick}
                disabled={loading}
                ghost={plan.id === subscriptionId || plan.price === 0}
                block
              >
                {plan.price === 0
                  ? formatMessage({ id: 'plan.free' })
                  : formatMessage({ id: 'plan.selectPlan' })}
              </Button>
            )}
          </>
        )}
      </StyledButtonContainer>
    </CardWrapper>
  );
};

export default PlanCard;
