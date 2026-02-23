import {Button} from 'antd';
import styled from 'styled-components';
import {rgba} from 'polished';
import {CirclePicker} from 'react-color';

/*
const CirclePicker = dynamic(
  () => import('react-color').then((colorPicker) => colorPicker.CirclePicker),
  {
    ssr: false,
  }
);
*/

/*const CirclePicker = dynamic(
  () => import('react-color').then((colorPicker) => colorPicker.CirclePicker),
  {
    ssr: false,
  }
);*/

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  background-color: ${({theme}: { theme: any }) =>
  rgba(theme.primaryColor, 0.11)};
  border: 1px solid ${({theme}: { theme: any }) => theme.border.color};
  border-radius: 8px;
  padding: 10px;
  overflow: hidden;
`;

const COLOR_PALETTE = [
  '#f44336',
  '#e91e63',
  '#9c27b0',
  '#673ab7',
  '#3f51b5',
  '#2196f3',
  '#03a9f4',
  '#00bcd4',
  '#009688',
  '#4caf50',
  '#8bc34a',
  '#cddc39',
  '#ffeb3b',
  '#ffc107',
  '#ff9800',
  '#ff5722',
  '#795548',
  '#607d8b',
  '#ffffff',
  '#1F1F1F',
  '#007FFF',
  '#666666',
  '#999999',
  '#CCCCCC',
];

type Props = {
  activeColor: string;
  type: 'text' | 'fill';
  onColorSelect: (color: string, type: 'text' | 'fill') => void;
};

const ColorPalette = ({activeColor, type, onColorSelect}: Props) => {
  return (
    <StyledRoot>
      <CirclePicker
        color={activeColor}
        onChange={(color: { hex: string }) => onColorSelect(color.hex, type)}
        colors={COLOR_PALETTE}
      />

      <Button
        type="primary"
        size="small"
        shape="round"
        onClick={() => onColorSelect('', type)}
        block
      >
        reset
      </Button>
    </StyledRoot>
  );
};

export default ColorPalette;
