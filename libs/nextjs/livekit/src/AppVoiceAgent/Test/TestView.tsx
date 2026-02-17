import { StyledAgentContainer, WidgetContainer } from './TestView.styled';
import { TestMetricsCard } from './TestMetricsCard';
import { ResponseType } from './TestAgent';

type TestViewProps = {
  agentName: string;
  response: ResponseType;
  setStartCall: (start: boolean) => void;
};

const TestView = ({ agentName, response, setStartCall }: TestViewProps) => {
  return (
    <WidgetContainer>
      <StyledAgentContainer direction="row">
        <TestMetricsCard
          onEndTest={() => {
            setStartCall(false);
          }}
          agentName={agentName}
          state={'Live'}
          response={response}
        ></TestMetricsCard>
      </StyledAgentContainer>
    </WidgetContainer>
  );
};

export default TestView;
