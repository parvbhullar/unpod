import { StyledAgentContainer, WidgetContainer } from './TestView.styled';
import { TestMetricsCard } from './TestMetricsCard';
import { ResponseType } from './TestAgent';

type TestViewProps = {
  agentName: string;
  response: ResponseType;
};

const TestView = ({ agentName, response }: TestViewProps) => {
  return (
    <WidgetContainer>
      <StyledAgentContainer direction="row">
        <TestMetricsCard
          agentName={agentName}
          state={'Live'}
          response={response}
        ></TestMetricsCard>
      </StyledAgentContainer>
    </WidgetContainer>
  );
};

export default TestView;
