import { Form } from 'antd';
import TemperatureSlider from '../../ModelForm/TemperatureSlider';
import {
  StyledContainer,
  StyledHelpText,
  StyledLabel,
  StyledlableWrapper,
} from './index.styled';
import { useIntl } from 'react-intl';

const { Item } = Form;

const StopSpeakingPlan = () => {
  const { formatMessage } = useIntl();

  return (
    <StyledContainer>
      <Item
        name="number_of_words"
        label={
          <StyledlableWrapper>
            <StyledLabel>
              {formatMessage({ id: 'advanced.numWords' })}
            </StyledLabel>
            <StyledHelpText>
              {formatMessage({ id: 'advanced.numWordsDesc' })}
            </StyledHelpText>
          </StyledlableWrapper>
        }
      >
        <TemperatureSlider
          marks={{
            0: {
              style: { fontSize: 12 },
              label: '0',
            },
            10: {
              style: { fontSize: 12, transform: 'translateX(-75%)' },
              label: '10',
            },
          }}
          max={10}
          step={1}
          text={false}
        />
      </Item>

      <Item
        name="voice_seconds"
        label={
          <StyledlableWrapper>
            <StyledLabel>
              {formatMessage({ id: 'advanced.voiceSec' })}
            </StyledLabel>
            <StyledHelpText>
              {formatMessage({ id: 'advanced.voiceSecDesc' })}
            </StyledHelpText>
          </StyledlableWrapper>
        }
      >
        <TemperatureSlider
          marks={{
            0: {
              style: { fontSize: 12, marginLeft: 16 },
              label: '0 (sec)',
            },
            5: {
              style: {
                fontSize: 12,
                transform: 'translateX(-75%)',
                minWidth: 60,
              },
              label: '0.5 (sec)',
            },
          }}
          max={5}
          step={1}
          text={false}
        />
      </Item>

      <Item
        name="back_off_seconds"
        label={
          <StyledlableWrapper>
            <StyledLabel>
              {formatMessage({ id: 'advanced.backOffSec' })}
            </StyledLabel>
            <StyledHelpText>
              {formatMessage({ id: 'advanced.backOffSecDesc' })}
            </StyledHelpText>
          </StyledlableWrapper>
        }
      >
        <TemperatureSlider
          marks={{
            0: {
              style: { fontSize: 12, marginLeft: 16 },
              label: '0 (sec)',
            },
            10: {
              style: {
                fontSize: 12,
                transform: 'translateX(-75%)',
                minWidth: 50,
              },
              label: '10 (sec)',
            },
          }}
          max={10}
          step={1}
          text={false}
        />
      </Item>
    </StyledContainer>
  );
};

export default StopSpeakingPlan;
