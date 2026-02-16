// import React from 'react';
// import EndCall from './Local/EndCall';
// /*import ChangeLayout from './Local/ChangeLayout';*/
// import LocalAudioMute from './Local/LocalAudioMute';
// import Screenshare from './Local/Screenshare';
// import LocalVideoMute from './Local/LocalVideoMute';
// import styled from 'styled-components';
// import RecordCall from './Local/RecordCall';
// import ShowPeople from './Local/ShowPeople';
// import { useStreamContext } from '../../../../../../apps/unpod/modules/Streaming/StreamContextProvider';
//
// export const StyledRoot = styled.div`
//   width: 100%;
//   height: 70px;
//   z-index: 100;
//   display: flex;
//   flex-direction: row;
//   align-items: center;
//   /*position: absolute;
//   bottom: 20px;
//   top: auto;*/
//   background-color: ${({ theme }) => theme.palette.background.default};
// `;
//
// export const StyledContainer = styled.div`
//   display: flex;
//   flex-direction: row;
//   justify-content: space-evenly;
//   align-items: center;
// `;
//
// function LocalControls({ isGrid }) {
//   const { role } = useStreamContext();
//   return (
//     <StyledRoot>
//       <StyledContainer
//         style={{
//           // flex: isLandscape.current ? 2 : 3,
//           flex: 1,
//         }}
//       >
//         {role !== 'audience' && <LocalAudioMute />}
//         {role !== 'audience' && <LocalVideoMute />}
//         {role !== 'audience' && <Screenshare />}
//         {/*<ChangeLayout />*/}
//         <RecordCall />
//         <EndCall />
//         <ShowPeople />
//         {/*<ShowChat />
//         <ShowPeople />*/}
//         {/*<Emoji />*/}
//         {/*<BtnTemplate name="more" />*/}
//       </StyledContainer>
//       {/*{!isGrid && <div style={{ flex: 1, padding: '0px 16px' }} />}*/}
//     </StyledRoot>
//   );
// }
//
// export default LocalControls;
import React from 'react';

const LocalControls = () => {
  return (
    <div>
      <h1>LocalControls</h1>
    </div>
  );
};

export default LocalControls;
