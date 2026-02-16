import { Fragment } from 'react';
import { convertMachineNameToName } from '@unpod/helpers/StringHelper';
import AppConnectorList from '@unpod/components/modules/AppConnectorList';
import { SITE_URL } from '@unpod/constants';
import {
  StyledButton,
  StyledConnector,
  StyledConnectorTitle,
  StyledContainer,
} from './index.style';

type ConnectorsProps = {
  currentKb?: { slug?: string };
  connector?: { app_slug?: string } | null;
  setOpenConnectors: (open: boolean) => void;
};

const Connectors = ({
  currentKb,
  connector,
  setOpenConnectors,
}: ConnectorsProps) => {
  return (
    <StyledContainer>
      {connector ? (
        <StyledConnector>
          Connected to{' '}
          <StyledConnectorTitle>
            {convertMachineNameToName(connector.app_slug)}
          </StyledConnectorTitle>
        </StyledConnector>
      ) : (
        <Fragment>
          <StyledButton shape="round" onClick={() => setOpenConnectors(true)}>
            Connect To
          </StyledButton>
          <AppConnectorList
            defaultPayload={{
              redirect_route: `${SITE_URL}/knowledge-bases/${currentKb?.slug || ''}/`,
              kb: currentKb?.slug || '',
            }}
          />
        </Fragment>
      )}
    </StyledContainer>
  );
};

export default Connectors;
