import { useState } from 'react';
import { Button, Col, Radio, Row } from 'antd';
import { AppInput, AppTextArea } from '@unpod/components/antd';
import SharedFields from '../SharedFields';

const { Button: RadioButton, Group } = Radio;

type SharedField = {
  email: string;
  role_code: string;
};

const WorkflowForm = () => {
  const [workflowType, setWorkflowType] = useState('public');
  const [sharedFields, setSharedFields] = useState<SharedField[]>([]);
  const [workflowData, setWorkflowData] = useState({
    name: '',
    handler: '',
    description: '',
  });
  void workflowData;

  const handleWorkflowTypeChange = (event: any) => {
    const { target } = event;
    setWorkflowType(target.value ?? 'public');
  };

  const handleChange = (event: any) => {
    const { target } = event;
    const { name, value } = target ?? {};
    if (name && value) {
      setWorkflowData((prevData) => ({ ...prevData, [name]: value }));
    }
  };
  return (
    <Row gutter={[24, 24]}>
      <Col span={12}>
        <AppInput
          placeholder="Workflow Name"
          name="name"
          onChange={handleChange}
        />
      </Col>
      <Col span={12}>
        <AppInput
          placeholder="Workflow handle"
          name="handler"
          onChange={handleChange}
        />
      </Col>
      <Col span={24}>
        <AppTextArea
          placeholder="Workflow Description"
          rows={4}
          name="description"
          onChange={handleChange}
        />
      </Col>
      <Col span={24}>
        <Group
          defaultValue={workflowType}
          size="large"
          onChange={handleWorkflowTypeChange}
        >
          <RadioButton value="public">Public</RadioButton>
          <RadioButton value="shared">Shared</RadioButton>
        </Group>
      </Col>
      {workflowType === 'shared' && (
        <Col span={24}>
          <SharedFields
            sharedFields={sharedFields}
            setSharedFields={setSharedFields}
          />
        </Col>
      )}
      <Col span={24}>
        <Button type="primary">Save</Button>
      </Col>
    </Row>
  );
};

export default WorkflowForm;
