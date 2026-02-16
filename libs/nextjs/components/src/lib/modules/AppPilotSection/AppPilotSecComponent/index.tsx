
import { Typography } from 'antd';
import FormInput from './inputs/FormInput';
import { StyledFieldList } from './index.styled';
import CardWrapper from '../../../common/CardWrapper';
import {
  MdBuild,
  MdCheckCircleOutline,
  MdDashboardCustomize,
  MdDescription,
} from 'react-icons/md';

const { Paragraph } = Typography;

const getIcon = (name: string) => {
  switch (name) {
    case 'Structured Data':
      return <MdDashboardCustomize size={18} />;
    case 'Success Evaluation':
      return <MdCheckCircleOutline size={18} />;
    case 'Summary':
      return <MdDescription size={18} />;
    default:
      return <MdBuild size={18} />;
  }
};

type PilotComponent = {
  name: string;
  slug?: string;
  description?: string;
  form_fields: any[];
  [key: string]: any;
};

type AppPilotSecComponentProps = {
  component: PilotComponent;
};

const AppPilotSecComponent = ({ component }: AppPilotSecComponentProps) => {
  return (
    <CardWrapper icon={getIcon(component.name)} title={component.name}>
      <Paragraph>
        <div
          dangerouslySetInnerHTML={{
            __html: component.description || '',
          }}
        />
      </Paragraph>

      <StyledFieldList>
        {component.form_fields.map((field: any, index: number) => (
          <FormInput key={index} component={component} field={field} />
        ))}
      </StyledFieldList>
    </CardWrapper>
  );
};

export default AppPilotSecComponent;
