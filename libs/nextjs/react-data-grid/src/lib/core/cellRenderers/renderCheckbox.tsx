import type { RenderCheckboxProps } from '../models/data-grid';
import { Checkbox, Radio } from 'antd';
import { CheckboxChangeEvent } from 'antd/es/checkbox';

export function renderCheckbox({ onChange, ...props }: RenderCheckboxProps) {
  function handleChange(e: CheckboxChangeEvent) {
    onChange(e.target.checked, (e.nativeEvent as MouseEvent).shiftKey);
  }

  return props.type === 'checkbox' ? (
    <Checkbox
      className="rdg-checkbox-input"
      checked={props.checked ?? false}
      onChange={handleChange}
      disabled={props.disabled}
    />
  ) : (
    <Radio
      className="rdg-checkbox-input"
      checked={props.checked ?? false}
      onChange={handleChange}
      disabled={props.disabled}
    />
  );
}
