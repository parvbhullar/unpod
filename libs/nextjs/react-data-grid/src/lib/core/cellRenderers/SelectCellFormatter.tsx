import type {RenderCheckboxProps} from '../models/data-grid';
import {useDefaultRenderers} from '../DataGridDefaultRenderersProvider';

type SharedInputProps = Pick<
  RenderCheckboxProps,
  'disabled' | 'tabIndex' | 'aria-label' | 'aria-labelledby'
>;

type SelectCellFormatterProps = SharedInputProps & {
  value: boolean;
  onChange: (value: boolean, isShiftClick: boolean) => void;
  type?: 'radio' | 'checkbox';
};

export function SelectCellFormatter({
                                      value,
                                      tabIndex,
                                      disabled,
                                      type,
                                      onChange,
                                      'aria-label': ariaLabel,
                                      'aria-labelledby': ariaLabelledBy,
                                    }: SelectCellFormatterProps) {
  const renderCheckbox = useDefaultRenderers()!.renderCheckbox!;

  return renderCheckbox({
    'aria-label': ariaLabel,
    'aria-labelledby': ariaLabelledBy,
    type: type,
    tabIndex,
    disabled,
    checked: value,
    onChange,
  });
}
