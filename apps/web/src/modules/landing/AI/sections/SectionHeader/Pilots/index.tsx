import React from 'react';
import { StyledRoot } from './index.styled';
import { Row, Typography } from 'antd';
import PilotCard from './PilotCard';
import { useGetDataApi } from '@unpod/providers';
import type { Pilot } from '@unpod/constants/types';

const { Title } = Typography;

type PilotsProps = {
  onPilotClick?: (pilot: Pilot) => void;
  heading?: React.ReactNode;
};

const Pilots: React.FC<PilotsProps> = ({ onPilotClick, heading }) => {
  const [{ apiData }] = useGetDataApi<Pilot[]>(`core/pilots/public/`, {
    data: [],
  });
  const pilots = apiData?.data ?? [];

  return (
    <StyledRoot>
      <Title level={2} className="text-center">
        {heading || '#Trending AIs'}
      </Title>

      <Row gutter={[16, 16]}>
        {pilots.map((pilot, index) => (
          <PilotCard key={index} pilot={pilot} onPilotClick={onPilotClick} />
        ))}
      </Row>
    </StyledRoot>
  );
};

export default Pilots;
