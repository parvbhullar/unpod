import React from 'react';
import JSONPretty from 'react-json-pretty';
import AppCopyToClipboard from '../AppCopyToClipboard';
import {StyledContainer, StyledCopyWrapper} from './index.styled';

type AppJsonViewerProps = {
  showCopyClipboard?: boolean;
  json: unknown;
  space?: number;
};

const AppJsonViewer: React.FC<AppJsonViewerProps> = ({
                                                       showCopyClipboard = false,
                                                       json,
                                                       space = 4,
                                                     }) => {
  return (
    <StyledContainer>
      {showCopyClipboard ? (
        <StyledCopyWrapper>
          <AppCopyToClipboard
            text={JSON.stringify(json, null, 2)}
            showToolTip
          />
        </StyledCopyWrapper>
      ) : null}
      <JSONPretty data={json} space={space}/>
    </StyledContainer>
  );
};

export default AppJsonViewer;
