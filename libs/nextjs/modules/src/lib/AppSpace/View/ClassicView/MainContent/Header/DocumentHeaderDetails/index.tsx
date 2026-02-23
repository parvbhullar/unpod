import {StyledEmailContainer, StyledEmailText, StyledFlexContainer, StyledHeaderSubtitle,} from './index.styled';
import {Flex} from 'antd';
import {IoCallOutline} from 'react-icons/io5';
import {MdMailOutline} from 'react-icons/md';

type DocumentHeaderDetailsProps = {
  subtitle?: string;
  email?: string;
  type?: string;
};

const DocumentHeaderDetails = ({
                                 subtitle,
                                 email,
                                 type = 'headerDetails',
                               }: DocumentHeaderDetailsProps) => (
  <>
    {
      type === 'headerDetails' ? (
        <StyledFlexContainer>
          <Flex align="center" gap={4}>
            <IoCallOutline size={11}/>
            <StyledHeaderSubtitle ellipsis={true}>
              {subtitle}
            </StyledHeaderSubtitle>
          </Flex>
          {email && (
            <StyledEmailContainer align="center" gap={4}>
              <MdMailOutline size={14}/>
              <StyledEmailText ellipsis={true}>{email}</StyledEmailText>
            </StyledEmailContainer>
          )}
        </StyledFlexContainer>
      ) : null
      // <Flex align={'center'} gap={10}>
      //   <StyledBadge>{isMobile ? 'VIP' : 'VIP Customer'}</StyledBadge>
      //   <StyledBadge className={'success'}>Active</StyledBadge>
      //   <StyledBadge className={'Enterprise'}>Enterprise</StyledBadge>
      // </Flex>
    }
  </>
);

export default DocumentHeaderDetails;
