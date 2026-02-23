import {useState} from 'react';
import {StyledHeaderActions, StyledHeaderIcon, StyledHeaderTitle, StyledMainHeaderContent,} from './index.styled';
import UserAvatar from '@unpod/components/common/UserAvatar';
import {getFirstLetter} from '@unpod/helpers/StringHelper';
import DocumentHeaderDetails from './DocumentHeaderDetails';
import AppSpaceContactCall from '@unpod/components/modules/AppSpaceContactCall';
import {useAppSpaceActionsContext, useAppSpaceContext,} from '@unpod/providers';
import {DesktopWidthQuery, XssMobileWidthQuery} from '@unpod/constants';
import {Flex} from 'antd';
import {MdCall} from 'react-icons/md';
import {useMediaQuery} from 'react-responsive';
import {AppDrawer} from '@unpod/components/antd';
import {AppHeaderButton} from '@unpod/components/common/AppPageHeader';
import DocSelector from '../Content/Calls/DocSelector';
import AppSpaceCallModal from '@unpod/components/modules/AppSpaceContactCall/AppSpaceCallModal';
import {useIntl} from 'react-intl';
import People from '../../Sidebar/People';

type HeaderInfo = {
  icon?: string;
  iconTooltip?: string;
  title?: string;
  subtitle?: string;
  email?: string;
  isUser?: boolean;
};

const getHeaderInfo = (currentData: any): HeaderInfo => {
  if (!currentData) {
    return {};
  }
  return {
    icon: currentData.name || 'DO',
    iconTooltip: currentData.name || '',
    title: currentData.name || 'Document',
    subtitle: currentData.contact_number,
    email: currentData.email,
    isUser: currentData.isUser,
  };
};

const ContactHeader = () => {
  const {activeDocument, currentSpace} = useAppSpaceContext();
  const {setActiveTab} = useAppSpaceActionsContext();
  const {formatMessage} = useIntl();

  const [open, setOpen] = useState(false);
  const [visible, setVisible] = useState(false);

  const isMobile = useMediaQuery(DesktopWidthQuery);
  const mobileView = useMediaQuery(XssMobileWidthQuery);

  const headerInfo = getHeaderInfo(activeDocument);

  const {icon, title, subtitle, email, isUser} = headerInfo;
  const spaceName =
    typeof currentSpace?.name === 'string' ? currentSpace.name : '';

  return (
    <>
      <StyledMainHeaderContent>
        {activeDocument ? (
          <Flex gap={mobileView ? 6 : 10} align="center">
            {isUser ? (
              <UserAvatar
                user={{full_name: icon || ''}}
                shape="square"
                size={32}
                fontSize={14}
              />
            ) : (
              <StyledHeaderIcon shape="square" size={32} data-icon={icon}>
                {getFirstLetter(icon)}
              </StyledHeaderIcon>
            )}
            <Flex vertical={true}>
              <StyledHeaderTitle level={2}>{title}</StyledHeaderTitle>
              <DocumentHeaderDetails subtitle={subtitle} email={email}/>
            </Flex>
          </Flex>
        ) : (
          <Flex gap={mobileView ? 6 : 10} align="center">
            <StyledHeaderIcon shape="square" size={32}>
              {getFirstLetter(spaceName)}
            </StyledHeaderIcon>
            <Flex vertical={true}>
              <StyledHeaderTitle level={2}>{spaceName}</StyledHeaderTitle>
            </Flex>
          </Flex>
        )}
      </StyledMainHeaderContent>

      {activeDocument ? (
        <StyledHeaderActions>
          <AppSpaceContactCall
            idKey="document_id"
            onFinishSchedule={() => {
              setActiveTab('call');
            }}
            data={activeDocument}
            hideExport
            type="doc"
            drawerChildren={<People/>}
          />
        </StyledHeaderActions>
      ) : (
        <AppHeaderButton
          type="primary"
          shape="round"
          onClick={() => setOpen(true)}
        >
          {formatMessage({id: 'spaceHeader.callNow'})}
        </AppHeaderButton>
      )}
      <AppDrawer
        open={open}
        onClose={() => setOpen(false)}
        closable={false}
        title={formatMessage({id: 'contactHeader.title'})}
        padding="0"
        overflowY="hidden"
        extra={
          <AppHeaderButton
            type="primary"
            shape={!isMobile ? 'round' : 'circle'}
            icon={
              <span className="anticon" style={{verticalAlign: 'middle'}}>
                <MdCall fontSize={!isMobile ? 16 : 22}/>
              </span>
            }
            onClick={() => setVisible(true)}
          >
            {!isMobile && formatMessage({id: 'spaceHeader.callNow'})}
          </AppHeaderButton>
        }
      >
        <DocSelector allowSelection/>
      </AppDrawer>

      <AppSpaceCallModal
        open={visible}
        setOpen={setVisible}
        idKey="document_id"
        onFinishSchedule={() => {
          console.log('Call scheduled');
        }}
      />
    </>
  );
};

export default ContactHeader;
