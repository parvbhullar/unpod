import AppPilotSecComponent from './AppPilotSecComponent';
import {StyledRoot} from './index.styled';

type AppPilotSectionProps = {
  section?: string;
  components?: any[];
};

const AppPilotSection = ({section, components}: AppPilotSectionProps) => {
  return (
    <StyledRoot>
      {/*<div>{section}</div>*/}

      {components?.map((component, index: number) => (
        <AppPilotSecComponent key={index} component={component}/>
      ))}
    </StyledRoot>
  );
};

export default AppPilotSection;
