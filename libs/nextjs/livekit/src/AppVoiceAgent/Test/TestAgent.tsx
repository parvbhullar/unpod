import {useState} from 'react';
import {TopContainer} from './TestView.styled';
import {TestAgentButton} from './TestAgentButton';
import PreviousTests from './PreviousTests';
import TestView from './TestView';
import {postDataApi, useInfoViewActionsContext} from '@unpod/providers';
import {Pilot, Spaces} from '@unpod/constants';

type TestAgentProps = {
  agentData?: Pilot;
  [key: string]: unknown;
};

export type ResponseType = {
  type: string;
  label: string;
};

const TestAgent = ({agentData, ...rest}: TestAgentProps) => {
  const [startCall, setStartCall] = useState<boolean>(false);
  const [response, setResponse] = useState<ResponseType>({
    type: '',
    label: '',
  });
  const infoViewActionsContext = useInfoViewActionsContext();

  const tokens = agentData?.kb_list?.map((item: Spaces) => item.token) ?? [];

  const onTest = () => {
    postDataApi(
      'core/tests/test-agent/',
      infoViewActionsContext,
      {
        agent_id: agentData?.handle,
        kn_bases: tokens,
      },
      true,
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        setStartCall(true);
        setResponse({
          type: 'success',
          label: response?.message || 'Test Started Successful',
        });
      })
      .catch((err: any) => {
        infoViewActionsContext.showError(err?.message || 'Test Failed');
        setResponse({
          type: 'error',
          label: err?.message || 'Test Failed',
        });
      });
  };

  return (
    <div>
      <TopContainer>
        <TestAgentButton
          {...rest}
          disable={startCall}
          onClick={() => onTest()}
        />
      </TopContainer>

      {startCall && (
        <TestView agentName={agentData?.name as string} response={response} setStartCall={setStartCall}/>
      )}

      <PreviousTests agentId={agentData?.handle} startCall={startCall}/>
    </div>
  );
};

export default TestAgent;
