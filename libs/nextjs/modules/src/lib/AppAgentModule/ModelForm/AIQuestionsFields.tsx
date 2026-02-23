import type {ChangeEvent, Dispatch, SetStateAction} from 'react';
import {useState} from 'react';
import {Button, Flex} from 'antd';
import {AppInput} from '@unpod/components/antd';
import styled from 'styled-components';

const AIQuestionsContainer = styled(Flex)`
  flex-direction: column;
  gap: 10px;
  height: 100%;
  max-height: 200px;
  overflow: auto;
  padding-top: 12px;
`;

type AIQuestionsFieldsProps = {
  questionsFields: string[];
  setQuestionsFields: Dispatch<SetStateAction<string[]>>;
};

const AIQuestionsFields = ({
                             questionsFields,
                             setQuestionsFields,
                           }: AIQuestionsFieldsProps) => {
  const [question, setQuestion] = useState('');

  const handleAddSharedField = () => {
    if (question.trim()) {
      setQuestionsFields((prevQuestions) => [...prevQuestions, question]);
      setQuestion('');
    }
  };

  const handleDeleteField = (index: number) => {
    setQuestionsFields((prevQuestions) =>
      prevQuestions.filter((_, i) => i !== index),
    );
  };

  const handleQuestionInput = (event: ChangeEvent<HTMLInputElement>) => {
    const {target} = event;
    setQuestion(target.value ?? '');
  };

  return (
    <Flex vertical gap="large">
      <Flex gap="large">
        <AppInput
          placeholder={`Enter Objective ${questionsFields.length + 1}`}
          value={question}
          onChange={handleQuestionInput}
        />
        <Button onClick={handleAddSharedField} disabled={!question.trim()}>
          Add
        </Button>
      </Flex>
      <AIQuestionsContainer>
        {questionsFields.map((ques, index) => (
          <Flex key={index} gap="large">
            <AppInput
              placeholder={`Objective ${index + 1}`}
              value={ques}
              disabled
            />
            <Button onClick={() => handleDeleteField(index)}>Delete</Button>
          </Flex>
        ))}
      </AIQuestionsContainer>
    </Flex>
  );
};
export default AIQuestionsFields;
