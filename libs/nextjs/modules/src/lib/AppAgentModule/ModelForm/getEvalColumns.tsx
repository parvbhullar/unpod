import { Flex, Typography } from 'antd';
import GenerateEvalButton from '@unpod/components/modules/GenerateEvalButton/GenerateEvalButton';
import type { ColumnsType } from 'antd/es/table';
import { AppStatusBadge } from '@unpod/components/common/AppStatusBadge';

const { Text } = Typography;


export type EvalRow = {
  key: string;
  type: 'agent' | 'kb';
  name: string;
  evalName?: string;
  evalSlug?: string;
  token: string;
  hasEval: boolean;
  status?: string | undefined;
};

export const getEvalColumns = (
  handleEvalResponse: (res: any, key: string) => void,
  formatMessage: any,
): ColumnsType<EvalRow> => {
  return [
    {
      title: 'Evals',
      dataIndex: 'evalName',
      key: 'evalName',
      render: (text: string) => <Text>{text || '-'}</Text>,
    },
    {
      title: formatMessage({ id: 'aiStudio.knowledgeBase' }),
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: formatMessage({ id: 'apiKey.actions' }),
      key: 'actions',
      render: (_: unknown, record: EvalRow) => (
        <Flex justify="center">
          {record.status !== 'pending' || record.status === undefined ? (
            <GenerateEvalButton
              type={record.type === 'agent' ? 'pilot' : 'knowledgebase'}
              token={record.token}
              buttonType="default"
              size="small"
              onClick={(response) => handleEvalResponse(response, record.key)}
              force={record.hasEval}
              text={record.hasEval ? 'common.refresh' : 'common.generateEvals'}
            />
          ) : (
            <AppStatusBadge status={record.status} name={record.status} />
          )}
        </Flex>
      ),
    },
  ];
};
