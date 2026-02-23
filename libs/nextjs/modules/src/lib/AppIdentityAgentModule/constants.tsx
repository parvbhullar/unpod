import Identity from '../AppAgentModule/Identity';
import Persona from './Persona';
import VoiceForm from './VoiceForm';

type FormatMessage = (descriptor: { id: string }) => string;

type GetTabItemsParams = {
  agentType?: string;
  isNewAgent?: boolean;
  formatMessage: FormatMessage;
  [key: string]: any;
};

export const getTabItems = ({
                              agentType,
                              isNewAgent,
                              formatMessage,
                              ...restProps
                            }: GetTabItemsParams) => {
  const items = [
    {
      key: 'identity',
      label: formatMessage({id: 'identityOnboarding.identity'}),
      children: <Identity {...restProps} />,
    },
    {
      key: 'persona',
      label: formatMessage({id: 'identityOnboarding.persona'}),
      disabled: isNewAgent,
      children: <Persona {...restProps} />,
    },
  ];

  if (agentType === 'Voice') {
    items.push({
      key: 'voice-profile',
      label: formatMessage({id: 'identityStudio.voiceProfile'}),
      disabled: isNewAgent,
      children: <VoiceForm {...restProps} />,
    });
  }

  return items;
};
