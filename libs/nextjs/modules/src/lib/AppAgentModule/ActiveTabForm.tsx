import Overview from './OverviewForm';
import WorkflowForm from './WorkflowForm';
import ModelForm from './ModelForm';
import VoiceForm from './VoiceForm';

type ActiveTabFormProps = {
  activeTab?: string;
  agentData?: any;
  updateAgentData?: (data: any) => void;
  headerForm?: any;
};

const ActiveTabForm = ({
                         activeTab,
                         agentData,
                         updateAgentData,
                         headerForm,
                       }: ActiveTabFormProps) => {
  const OverviewComponent = Overview as any;
  const ModelComponent = ModelForm as any;
  const VoiceComponent = VoiceForm as any;
  const WorkflowComponent = WorkflowForm as any;

  switch (activeTab) {
    case 'overview':
      return (
        <OverviewComponent
          agentData={agentData}
          updateAgentData={updateAgentData}
          headerForm={headerForm}
        />
      );
    case 'model':
      return (
        <ModelComponent
          agentData={agentData}
          updateAgentData={updateAgentData}
        />
      );
    case 'voice':
      return (
        <VoiceComponent
          agentData={agentData}
          updateAgentData={updateAgentData}
        />
      );
    case 'workflow':
      return (
        <WorkflowComponent
          agentData={agentData}
          updateAgentData={updateAgentData}
        />
      );
    default:
      return null;
  }
};

export default ActiveTabForm;
