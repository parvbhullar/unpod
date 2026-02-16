import React, { useMemo } from 'react';
import { Flex, Typography } from 'antd';
import {
  StyledFlex,
  TestCard,
  TestInfo,
  TestMeta,
} from './PreviousTests.styled';
import { TestResultProps } from '@unpod/constants';
import { AppStatusBadge } from '@unpod/components/common/AppStatusBadge';
import { AiOutlineLineChart } from 'react-icons/ai';
import { FaFileAlt, FaPhone, FaSignOutAlt, FaUserAlt } from 'react-icons/fa';
import AppList from '@unpod/components/common/AppList';

const { Text, Paragraph } = Typography;

type TestResultItemProps = {
  item: TestResultProps;
};

const getNameFromSlug = (slug?: string | null) => {
  if (!slug) return null;

  const parts = slug.split('_'); // split by underscore

  return parts
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1)) // capitalize each word
    .join(' '); // join with space
};

const getIcon = (type: string | null) => {
  switch (type) {
    case 'Get Docs':
      return <FaFileAlt />;
    case 'Create Followup Or Callback':
      return <FaPhone />;
    case 'Handover ToolRecord User Info':
      return <FaUserAlt />;
    case 'End Call':
      return <FaSignOutAlt />;
    default:
      return <FaFileAlt />;
  }
};

type Field = {
  label: string;
  value: string | number | null | undefined;
};

const TestResultItem = ({ item }: TestResultItemProps) => {
  const fields: Field[] = [
    { label: 'Question', value: item?.question },
    { label: 'Expected Answer', value: item?.expected_answer },
    { label: 'Intent', value: item?.intent },
    { label: 'Actual Response', value: item?.actual_response },
    { label: 'Error', value: item?.error_message },
  ];

  const formattedToolName = useMemo(() => {
    return getNameFromSlug(item?.expected_tool);
  }, [item?.expected_tool]);

  return (
    <TestCard>
      <TestInfo>
        <StyledFlex
          justify="space-between"
          align="center"
          $mb={12}
        >
          <Text strong>TestResult #0{item?.test_case_index}</Text>
          <AppStatusBadge
            status={item?.passed === true ? 'badge-success' : 'badge-error'}
            name={item?.passed === true ? 'Passed' : 'Failed'}
            size="small"
            shape="round"
          />
        </StyledFlex>
        <Flex vertical align="left">
          <AppList
            data={fields || []}
            renderItem={(item: Field, index: number) => (
              <div key={`${item.label}-${index}`}>
                <Text strong>{item.label}</Text>
                <Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2, expandable: true, symbol: 'More' }}
                >
                  {item.value || '-'}
                </Paragraph>
              </div>
            )}
          />
        </Flex>
        <TestMeta>
          <Flex align="center" gap={6}>
            <AiOutlineLineChart size={14} />
            <Text type="secondary">
              {item?.answer_similarity_score?.toFixed(2)} Similarity Score
            </Text>
          </Flex>
          <Flex align="center" gap={6}>
            {getIcon(formattedToolName)}
            <Text type="secondary">{formattedToolName}</Text>
          </Flex>
        </TestMeta>
      </TestInfo>
    </TestCard>
  );
};

export default React.memo(TestResultItem);
