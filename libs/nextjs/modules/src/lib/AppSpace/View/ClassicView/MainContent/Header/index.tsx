import {StyledMainHeader, StyledRoot} from './index.styled';
import {useAppSpaceContext} from '@unpod/providers';
import EntityHeader from './EntityHeader';
import CallHeader from './CallHeader';
import ContactHeader from './ContactHeader';
import type {ReactNode} from 'react';

type HeaderProps = {
  taskCallButton?: ReactNode;
  onAddClick: (key: string) => void;
};

const Header = ({taskCallButton, onAddClick}: HeaderProps) => {
  const {activeTab} = useAppSpaceContext();

  const getHeaderContent = () => {
    switch (activeTab) {
      case 'call':
        return <CallHeader/>;
      case 'doc':
        return <ContactHeader/>;
    }
    return (
      <EntityHeader onAddClick={onAddClick} taskCallButton={taskCallButton}/>
    );
  };
  return (
    <StyledRoot>
      <StyledMainHeader>{getHeaderContent()}</StyledMainHeader>
    </StyledRoot>
  );
};

export default Header;
