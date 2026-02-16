import { Col } from 'antd';
import {
  MdOutlineArrowForward,
  MdOutlineMicNone,
  MdOutlinePhone,
} from 'react-icons/md';
import { AiOutlineSafety } from 'react-icons/ai';
import { AppGridContainer } from '@unpod/components/antd';
import TabCard from './TabCard';
import {
  StyledDescription,
  StyledGetStartedButton,
  StyledRoot,
  StyledSectionCard,
  StyledSectionParagraph,
} from './index.styled';
import { useIntl } from 'react-intl';

type FormatMessage = (descriptor: { id: string }) => string;

const getInfoCardData = (formatMessage: FormatMessage) => {
  const infoCards = [
    {
      key: 'telephony',
      icon: <MdOutlinePhone fontSize={42} />,
      title: formatMessage({ id: 'bridgeNew.telephonyTitle' }),
      description: (
        <StyledDescription>
          {formatMessage({ id: 'bridgeNew.telephonyDesc' })}
        </StyledDescription>
      ),
    },
    {
      key: 'voice',
      icon: <MdOutlineMicNone fontSize={42} />,
      title: formatMessage({ id: 'bridgeNew.voiceTitle' }),
      description: (
        <StyledDescription>
          {formatMessage({ id: 'bridgeNew.voiceDesc' })}
        </StyledDescription>
      ),
    },
    {
      key: 'kyc',
      icon: <AiOutlineSafety fontSize={42} />,
      title: formatMessage({ id: 'bridgeNew.kycTitle' }),
      description: (
        <StyledDescription>
          {formatMessage({ id: 'bridgeNew.kycDesc' })}
        </StyledDescription>
      ),
    },
  ];

  return infoCards;
};

type OverviewTabProps = {
  headerRef?: any;
  isNewRecord?: boolean;
};

const OverviewTab = ({ headerRef, isNewRecord }: OverviewTabProps) => {
  const { formatMessage } = useIntl();
  return (
    <StyledRoot>
      <StyledSectionCard>
        {/* <Title level={4}>How it works</Title> */}
        <StyledSectionParagraph>
          {formatMessage({ id: 'bridgeNew.overviewDescription' })}
        </StyledSectionParagraph>
      </StyledSectionCard>

      <AppGridContainer gutter={[24, 24]}>
        {getInfoCardData(formatMessage).map((item, index) => (
          <Col lg={24} xl={8} key={index}>
            <TabCard className={item.key} item={item} />
          </Col>
        ))}
      </AppGridContainer>
      {isNewRecord && (
        <div className="text-center">
          <StyledGetStartedButton
            icon={<MdOutlineArrowForward fontSize={16} />}
            onClick={() => headerRef?.current?.onSaveHeaderData()}
          >
            {formatMessage({ id: 'bridgeNew.getStarted' })}
          </StyledGetStartedButton>
        </div>
      )}
    </StyledRoot>
  );
};

export default OverviewTab;
