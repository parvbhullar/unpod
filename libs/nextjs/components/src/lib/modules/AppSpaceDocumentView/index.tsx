import ContactView from './ContactView';
import EmailThread from './EmailThread';
import GeneralDocView from './GeneralDocView';
import {useAppSpaceContext} from '@unpod/providers';

const DOCUMENT_VIEW_COMPONENTS = {
  contact: ContactView,
  email: EmailThread,
  general: GeneralDocView,
};

const AppSpaceDocumentView = () => {
  const {currentSpace} = useAppSpaceContext();
  const contentType = currentSpace?.content_type as
    | keyof typeof DOCUMENT_VIEW_COMPONENTS
    | undefined;
  const DocumentView = contentType
    ? DOCUMENT_VIEW_COMPONENTS[contentType]
    : GeneralDocView;
  return <DocumentView/>;
};

export default AppSpaceDocumentView;
