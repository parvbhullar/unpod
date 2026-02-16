import { Flex, InputNumber, Slider, Typography } from 'antd';
import styled from 'styled-components';
import type { CSSProperties } from 'react';
import { useIntl } from 'react-intl';

const CustomSlider = styled(Slider)`
  flex: 1;
  margin-right: 16px;

  .ant-slider-track {
    background-color: ${({ theme }) => theme.palette.primary} !important;
  }

  .ant-slider-rail {
    background-color: #796cff33 !important;
  }

  .ant-slider-dot-active {
    border-color: ${({ theme }) => theme.palette.primary} !important;
  }
`;

type TemperatureSliderProps = {
  value?: number;
  onChange?: (value: number | null) => void;
  text?: boolean;
  marks?: Record<number, { style?: CSSProperties; label: string }>;
  min?: number;
  max?: number;
  step?: number;
};

const TemperatureSlider = ({
  value,
  onChange,
  text = true,
  marks,
  min = 0,
  max = 1,
  step = 0.01,
}: TemperatureSliderProps) => {
  const { formatMessage } = useIntl();

  return (
    <>
      {text && (
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {formatMessage({ id: 'temperature.text' })}
        </Typography.Text>
      )}
      <Flex align="center" style={{ width: '100%' }}>
        <CustomSlider
          min={min}
          max={max}
          marks={marks}
          step={step}
          value={value}
          onChange={onChange}
        />

        <InputNumber
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={onChange}
          style={{ width: 70 }}
          size="large"
        />
      </Flex>
    </>
  );
};
export default TemperatureSlider;
