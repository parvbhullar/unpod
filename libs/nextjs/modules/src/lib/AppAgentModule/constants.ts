import type { Pilot } from '@unpod/constants/types';
import type { FormInstance } from 'antd';

type GetTabItemsParams = {
  agentType?: string;
  isNewAgent?: boolean;
  agentData: Pilot;
  updateAgentData?: (data: FormData) => void;
  headerForm?: FormInstance;
};

export const getTabItems = ({
  agentType,
  isNewAgent,
  agentData,
  updateAgentData,
  headerForm,
}: GetTabItemsParams) => {
  void agentType;
  void isNewAgent;
  void agentData;
  void updateAgentData;
  void headerForm;
  return [];
};
