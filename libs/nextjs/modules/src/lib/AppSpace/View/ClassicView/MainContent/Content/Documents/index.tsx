import DocumentView from './DocumentView';
import {StyledDetailsRoot} from './index.styled';
import {useAppSpaceContext} from '@unpod/providers';
import People from '../People';

const Documents = () => {
  const {documentMode, activeDocument} = useAppSpaceContext();

  return activeDocument && documentMode === 'view' ? (
    <StyledDetailsRoot>
      <People/>
    </StyledDetailsRoot>
  ) : (
    <DocumentView/>
  );
};

export default Documents;
