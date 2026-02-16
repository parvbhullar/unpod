import React from 'react';
import { StyledCard, StyledCardIcon } from './index.styled';
import { Card } from 'antd';

const { Meta } = Card;

type CreationMethod = {
  id: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  IconBgColor?: string;
  type: string;
};

type AllIdentityCardProps = {
  creationMethods: CreationMethod[];
  selectedCard?: string;
  setSelectedCard: (value: string) => void;
};

const AllIdentityCard: React.FC<AllIdentityCardProps> = ({
  creationMethods,
  selectedCard,
  setSelectedCard,
}) => {
  return (
    <>
      {creationMethods.map((creationMethod) => (
        <StyledCard
          as="button"
          key={creationMethod.id}
          onClick={() => setSelectedCard(creationMethod.type)}
          className={selectedCard === creationMethod.type ? 'selected' : ''}
        >
          <StyledCardIcon $bgColor={creationMethod.IconBgColor}>
            {creationMethod.icon}
          </StyledCardIcon>
          <Meta
            title={creationMethod.title}
            description={creationMethod.description}
          />
        </StyledCard>
      ))}
    </>
  );
};

export default AllIdentityCard;
