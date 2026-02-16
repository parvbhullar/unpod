import React from 'react';
import { Col, Tooltip } from 'antd';
import {
  StyledContent,
  StyledPilotCard,
  StyledSubTitle,
  StyledTitle,
  StylesImageWrapper,
} from './index.styled';
import AppImage from '@unpod/components/next/AppImage';
import type { Pilot } from '@unpod/constants/types';
/*import { FiArrowUpRight } from 'react-icons/fi';
import { useRouter } from 'next/navigation'*/

type PilotCardProps = {
  pilot: Pilot;
  onPilotClick?: (pilot: Pilot) => void;
};

const PilotCard: React.FC<PilotCardProps> = ({ pilot, onPilotClick }) => {
  // const router = useRouter();

  /*const onViewClick = () => {
    router.push(`/superbooks/${pilot.handle}/`);
  };*/

  return (
    <Col xs={24} sm={12} md={8}>
      <StyledPilotCard onClick={() => onPilotClick?.(pilot)}>
        <StylesImageWrapper>
          <AppImage
            src={
              pilot?.logo
                ? `${pilot.logo}?tr=w-40,h-40`
                : '/images/logo_avatar.png'
            }
            alt="logo"
            height={40}
            width={40}
            layout="fill"
            objectFit="cover"
          />
        </StylesImageWrapper>
        <StyledContent>
          <Tooltip title={pilot.name}>
            <StyledTitle>{pilot.name}</StyledTitle>
          </Tooltip>

          <Tooltip title={pilot.handle}>
            <StyledSubTitle>{pilot?.handle}</StyledSubTitle>
          </Tooltip>
        </StyledContent>

        {/*<StyledActions>
          <Tooltip title="Click to View">
            <Button type="default" shape="round" onClick={onViewClick}>
              <FiArrowUpRight fontSize={16} />
            </Button>
          </Tooltip>
        </StyledActions>*/}
      </StyledPilotCard>
    </Col>
  );
};

export default PilotCard;
