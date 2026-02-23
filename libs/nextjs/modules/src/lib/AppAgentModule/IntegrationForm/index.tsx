import {Button, Flex, Form, FormInstance} from 'antd';
import AppPilotSection from '@unpod/components/modules/AppPilotSection';
import {useInfoViewContext} from '@unpod/providers';
import {SaveOutlined} from '@ant-design/icons';
import {AnalysisItem, INPUT_DEFAULT_VALUES, TYPE_BASED_DEFAULT_VALUES,} from '@unpod/constants';
import {StickyFooter, StyledMainContainer, StyledTabRoot,} from '../index.styled';
import {useIntl} from 'react-intl';
import type {FormField, IntegrationItem, Pilot} from '@unpod/constants/types';

const {useForm} = Form;

type IntegrationFormProps = {
  agentData: Pilot;
  updateAgentData?: (data: FormData) => void;
  headerForm?: FormInstance;
};

type FormValue = {
  name?: string;
  components?: {
    Analysis?: AnalysisItem[];
    Integration?: IntegrationItem[];
  };
};

const IntegrationForm = ({
                           agentData,
                           updateAgentData,
                         }: IntegrationFormProps) => {
  const infoViewContext = useInfoViewContext();
  const [form] = useForm();
  const {formatMessage} = useIntl();

  const onFinish = (values: FormValue) => {
    // Handle form submission
    const formData = new FormData();
    formData.append('name', agentData?.name || '');
    formData.append('components', JSON.stringify(values));
    updateAgentData?.(formData);
  };

  const getInitialValues = () => {
    const initialValues: Record<string, any> = {};

    if (agentData?.components && agentData.components['Integration']) {
      agentData.components['Integration'].forEach(
        (component: IntegrationItem) => {
          const values = component.form_values?.values || {};
          component.form_fields.forEach((field: FormField) => {
            const defaultValue =
              INPUT_DEFAULT_VALUES[field.default as any] ||
              TYPE_BASED_DEFAULT_VALUES[field.type] ||
              '';
            initialValues[`${component.slug}__${field.name}`] =
              values[field.name] || defaultValue;
          });
        },
      );
    }

    return initialValues;
  };

  return (
    <Form
      layout="vertical"
      form={form}
      onFinish={onFinish}
      initialValues={getInitialValues()}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          {agentData?.components && agentData.components['Integration'] && (
            <AppPilotSection
              section="Integration"
              components={agentData.components['Integration'] || []}
            />
          )}
        </StyledMainContainer>
      </StyledTabRoot>

      <StickyFooter>
        <Flex justify="end">
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined/>}
            loading={infoViewContext.loading}
          >
            {formatMessage({id: 'common.save'})}
          </Button>
        </Flex>
      </StickyFooter>
    </Form>
  );
};

export default IntegrationForm;
