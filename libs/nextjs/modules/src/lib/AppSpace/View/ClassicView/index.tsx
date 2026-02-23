import {StyledRightPanel, StyledThreadContainer} from './index.styled';
import MainContent from './MainContent';
import {StyledPageContainer} from '../index.styled';

const ClassicView = () => {
  return (
    <StyledPageContainer>
      <StyledThreadContainer>
        <StyledRightPanel>
          <MainContent/>
        </StyledRightPanel>
      </StyledThreadContainer>
    </StyledPageContainer>
  );
};

export default ClassicView;
