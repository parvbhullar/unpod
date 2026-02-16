import PlanCard from './PlanCard';
import { StyledContainer, StyledListContainer } from './index.styled';

type PlanListProps = {
  plans: any[];
  loading?: boolean;
  onActivatePlan?: (plan: any) => void;
  onCancelSubscription?: (plan: any) => void;
  onContactPlan?: (plan: any) => void;
};

const PlanList = ({
  plans,
  loading,
  onActivatePlan,
  onCancelSubscription,
  onContactPlan,
}: PlanListProps) => {
  return (
    <StyledContainer>
      <StyledListContainer>
        {plans.map((plan: any, index: number) => (
          <PlanCard
            key={index}
            plan={plan}
            loading={loading}
            onActivatePlan={onActivatePlan}
            onCancelSubscription={onCancelSubscription}
            onContactPlan={onContactPlan}
          />
        ))}
      </StyledListContainer>
    </StyledContainer>
  );
};

export default PlanList;
