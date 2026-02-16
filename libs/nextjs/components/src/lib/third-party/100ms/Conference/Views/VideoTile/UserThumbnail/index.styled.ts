import styled from 'styled-components';

export const AvatarContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translateX(-50%) translateY(-50%);
  width: 40%;
  height: 40%;
  border-radius: 50%;
  overflow: hidden;

  & > span {
    max-height: 5rem;
    height: 100%;
  }
`;
