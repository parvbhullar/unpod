export type TestResultProps = {
  test_case_index: number;
  question: string;
  expected_answer: string;
  intent: string;
  passed: boolean;
  actual_response: string;
  error_message: string | null;
  tool_called: string | null;
  expected_tool: string | null;
  answer_similarity_score: number;
  answer_match_details: string | null;
};

export type TestItem = {
  created: string;
  modified: string;
  eval_id: string;
  agent_id: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: string;
  test_results: TestResultProps[];
  eval_timestamp: string;
  status?: string;
  metadata: {
    knowledge_bases: string[];
    test_case_count: number;
  };
  [key: string]: unknown;
};
