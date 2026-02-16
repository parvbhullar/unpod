// import React from "react";
// import styled from "styled-components";
// import { FiPhone, FiChevronDown } from "react-icons/fi";
//
// const WidgetContainer = styled.div`
//   display: flex;
//   align-items: center;
//   background: white;
//   padding: 1rem;
//   border-radius: 2rem;
//   box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
//   width: fit-content;
//   gap: 1rem;
// `;
//
// const Avatar = styled.div`
//   width: 48px;
//   height: 48px;
//   border-radius: 50%;
//   overflow: hidden;
//   border: 2px solid #ccc;
//   img {
//     width: 100%;
//     height: 100%;
//     object-fit: cover;
//   }
// `;
//
// const InfoSection = styled.div`
//   display: flex;
//   flex-direction: column;
//   gap: 0.4rem;
// `;
//
// const Label = styled.div`
//   font-size: 14px;
//   font-weight: 500;
//   color: #000;
// `;
//
// const VoiceButton = styled.button`
//   display: flex;
//   align-items: center;
//   background: #000;
//   color: white;
//   padding: 0.6rem 1.2rem;
//   border: none;
//   border-radius: 2rem;
//   cursor: pointer;
//   font-size: 14px;
//   gap: 0.5rem;
//
//   svg {
//     stroke-width: 2;
//   }
// `;
//
// const LanguageSelect = styled.button`
//   display: flex;
//   align-items: center;
//   gap: 0.3rem;
//   padding: 0.4rem 0.8rem;
//   border: 1px solid #ddd;
//   border-radius: 2rem;
//   background: white;
//   cursor: pointer;
//   box-shadow: 0 0 3px rgba(0, 0, 0, 0.05);
//
//   img {
//     width: 18px;
//     height: 18px;
//     border-radius: 50%;
//   }
//
//   svg {
//     stroke-width: 2;
//   }
// `;
//
// export const ChatWidget = () => {
//     return (
//         <WidgetContainer>
//             <Avatar>
//                 <img src="https://upload.wikimedia.org/wikipedia/commons/3/3f/Disc-icon.svg" alt="Agent" />
//             </Avatar>
//             <InfoSection>
//                 <Label>Need help?</Label>
//                 <VoiceButton>
//                     <FiPhone />
//                     Voice chat
//                 </VoiceButton>
//             </InfoSection>
//             <LanguageSelect>
//                 <img src="https://flagcdn.com/us.svg" alt="EN" />
//                 <FiChevronDown />
//             </LanguageSelect>
//         </WidgetContainer>
//     );
// };
