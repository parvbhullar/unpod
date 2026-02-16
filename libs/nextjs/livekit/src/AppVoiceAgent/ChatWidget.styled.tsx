import styled from 'styled-components';

export const WidgetContainer = styled.div`
  display: flex;
  align-items: center;
  background: white;
  padding: 1rem;
  width: fit-content;
  gap: 1rem;
`;

export const Avatar = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #ccc;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`;

export const InfoSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
`;

export const Label = styled.div`
  font-size: 14px;
  font-weight: 500;
  color: #000;
`;

export const LanguageSelect = styled.button`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  border: 1px solid #ddd;
  border-radius: 2rem;
  background: white;
  cursor: pointer;
  box-shadow: 0 0 3px rgba(0, 0, 0, 0.05);

  img {
    width: 18px;
    height: 18px;
    border-radius: 50%;
  }

  svg {
    stroke-width: 2;
  }
`;
export const WaveComponent = styled.div`
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: conic-gradient(
    from 0deg,
    #000000,
    #333333,
    #ffffff,
    #777777,
    #000000,
    #ffffff,
    #333333,
    #000000
  );
  filter: blur(0.5px) contrast(130%);
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
  animation: rotateWave 5s linear infinite;

  @keyframes rotateWave {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
`;
