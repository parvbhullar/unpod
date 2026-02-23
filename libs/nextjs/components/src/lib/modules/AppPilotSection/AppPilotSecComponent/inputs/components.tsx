import type {ReactElement} from 'react';
import {useCallback, useEffect, useState} from 'react';
import {Button, Flex, Form, InputNumber, Select, Switch} from 'antd';
import {MdAdd, MdDelete} from 'react-icons/md';

import {randomId} from '@unpod/helpers/GlobalHelper';
import {getMachineName} from '@unpod/helpers/StringHelper';
import {generateKbSchema, getKbInputsStructure, type KbInput,} from '@unpod/helpers/AppKbHelper';

import AppTextArea from '../../../../antd/AppTextArea';
import AppInput from '../../../../antd/AppInput';
import AppSelect from '../../../../antd/AppSelect';
import {AppInputSelector} from '../../../../antd';
import AppInputRow from '../../../../common/AppInputRow';
import AppRowOptions from '../../../../common/AppInputRow/AppRowOptions';
import {StyledItemRow, StyledList, StyledSlider} from './index.styled';

const {Option} = Select;
const {Item} = Form;

type FieldConfig = {
  labels?: [string, string];
  value_key?: string;
  label_key?: string | { title: string; description: string };
  columns?: InputColumn[];
  marks_label?: string;
  marks?: Record<number, { label: string; style?: Record<string, any> }>;
  min?: number;
  max?: number;
  step?: number;
  attributes?: Record<string, any>;
};

type FieldOption = Record<string, any>;

type InputField = {
  type: string;
  name?: string;
  title?: string;
  placeholder?: string;
  required?: boolean;
  config?: FieldConfig;
  options?: FieldOption[];
  description?: string;
  isEnum?: boolean;
};

type InputColumn = InputField & { name: string };

type InputComponentProps = {
  field: InputField;
  value?: any;
  onChange?: (value: any) => void;
  [key: string]: any;
};

type KbInputExtended = KbInput & { placeholder?: string };

type InputRowItem = {
  id?: number;
  name?: string;
  title?: string;
  type?: string;
  placeholder?: string;
  description?: string;
  required?: boolean;
  isEnum?: boolean;
  choices?: string[];
  defaultValue?: unknown;
};

export const InputText = ({field, ...restProps}: InputComponentProps) => {
  return (
    <AppInput
      placeholder={field.placeholder || field.title || ''}
      {...restProps}
    />
  );
};

const InputSwitch = ({field, ...restProps}: InputComponentProps) => {
  const [labelChecked = 'Yes', labelUnChecked = 'No'] =
  field?.config?.labels || [];
  return (
    <Switch
      checkedChildren={labelChecked}
      unCheckedChildren={labelUnChecked}
      {...restProps}
    />
  );
};

const InputSelect = ({field, ...restProps}: InputComponentProps) => {
  const value_key: string = field?.config?.value_key || 'value';
  const label_key: string | { title: string; description: string } =
    field?.config?.label_key || 'label';

  const renderLabel = (option: FieldOption) => {
    if (typeof label_key === 'object') {
      return (
        <div>
          <strong>{option[label_key['title']]}</strong>
          <div>{option[label_key['description']]}</div>
        </div>
      );
    }
    return option[label_key];
  };

  return (
    <AppSelect
      placeholder={field.placeholder || field.title || ''}
      optionLabelProp={value_key}
      {...restProps}
    >
      {(field.options || []).map((option: FieldOption, index: number) => (
        <Option key={index} value={option[value_key]}>
          {renderLabel(option)}
        </Option>
      ))}
    </AppSelect>
  );
};

const InputTextarea = ({field, ...restProps}: InputComponentProps) => {
  return (
    <AppTextArea
      placeholder={field.placeholder || field.title || ''}
      rows={4}
      autoSize={{minRows: 4, maxRows: 6}}
      {...restProps}
    />
  );
};

const InputSliderNumber = ({field, value, onChange}: InputComponentProps) => {
  const firstLabelStyle = {fontSize: 12, marginLeft: 16};
  const lastLabelStyle = {
    fontSize: 12,
    minWidth: 60,
    transform: 'translateX(-75%)',
  };

  const {
    min = 0,
    max = 1,
    step = 0.01,
    marks_label = '',
    marks = {
      [min]: {label: `${min} ${marks_label}`, style: firstLabelStyle},
      [max]: {label: `${max} ${marks_label}`, style: lastLabelStyle},
    },
  } = field.config || {};

  return (
    <Flex align="center">
      <StyledSlider
        min={min}
        max={max}
        marks={marks}
        step={step}
        value={value}
        onChange={onChange}
      />

      <InputNumber
        min={0}
        max={max}
        step={step}
        value={value}
        onChange={onChange}
        style={{width: 70}}
        size="large"
      />
    </Flex>
  );
};

const InputRepeaterItem = ({
                             name,
                             column,
                             ...restField
                           }: {
  name: number;
  column: InputColumn;
  [key: string]: any;
}) => {
  const InputComponent =
    (INPUT_COMPONENTS as Record<string, (props: any) => ReactElement>)[
      column.type
      ] || InputText;

  return (
    <Item
      {...restField}
      name={[name, column.name]}
      rules={[
        {
          required: column.required,
          message: 'This field is required',
        },
      ]}
    >
      <InputComponent field={column}/>
    </Item>
  );
};

const InputRepeater = ({
                         field,
                         fields,
                         remove,
                       }: {
  field: InputField;
  fields: Array<{ key: number; name: number; [key: string]: any }>;
  remove: (index: number) => void;
}) => {
  const columns = field?.config?.columns || [];
  const style = {
    gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr)) auto`,
  };

  return (
    <>
      {fields.map(({key, name, ...restField}) => (
        <StyledItemRow key={key} style={style}>
          {columns.map((column: InputColumn, index: number) => (
            <InputRepeaterItem
              key={index}
              name={name}
              column={column}
              {...restField}
            />
          ))}

          <Item>
            <Button
              type="primary"
              onClick={() => remove(name)}
              icon={<MdDelete fontSize={18}/>}
              danger
              ghost
            />
          </Item>
        </StyledItemRow>
      ))}
    </>
  );
};

const InputJson = ({field, value, onChange}: InputComponentProps) => {
  const [formInputs, setFormInputs] = useState<KbInputExtended[]>([]);
  const [open, setOpen] = useState(false);
  const [openDetail, setOpenDetail] = useState(false);
  const [selectedItem, setSelectedItem] = useState<InputRowItem | undefined>(
    undefined,
  );

  useEffect(() => {
    if (value) {
      setFormInputs(getKbInputsStructure(value) as KbInputExtended[]);
    }
  }, []);

  useEffect(() => {
    if (formInputs.length > 0) {
      const schemaInputs = formInputs.map((input) => ({
        name: input.name,
        type: input.type,
        title: input.title,
        description: input.description,
        defaultValue:
          typeof input.defaultValue === 'string' ? input.defaultValue : '',
        isEnum: input.isEnum,
        choices: input.choices,
        required: input.required,
      }));
      onChange?.(generateKbSchema(schemaInputs));
    }
  }, [formInputs]);

  const handleDeleteInput = (item: InputRowItem) => {
    if (item.id == null) return;
    setFormInputs((fields) => fields.filter((task) => item.id !== task.id));
  };

  const onRowReorder = useCallback((dragIndex: number, hoverIndex: number) => {
    setFormInputs((fields) => {
      const newItems = [...fields];
      const dragItem = fields[dragIndex];
      newItems.splice(dragIndex, 1);
      newItems.splice(hoverIndex, 0, dragItem);

      return newItems;
    });
  }, []);

  const handleRequiredChange = (checked: boolean, item: InputRowItem) => {
    if (item.id == null) return;
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          return {...data, required: checked};
        }

        return data;
      }),
    );
  };

  const handleEnumChange = (checked: boolean, item: InputRowItem) => {
    if (item.id == null) return;
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          return {...data, isEnum: checked};
        }

        return data;
      }),
    );
  };

  const handleDescriptionChange = (newValue: string, item: InputRowItem) => {
    if (item.id == null) return;
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          return {...data, description: newValue};
        }

        return data;
      }),
    );
  };

  const handleInputChange = (newValue: string, item: InputRowItem) => {
    if (item.id == null) return;
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          return {
            ...data,
            title: newValue,
            name: data.name || (newValue ? getMachineName(newValue) : ''),
          };
        }

        return data;
      }),
    );
  };

  const onFinishDetails = (values: Partial<KbInputExtended>) => {
    if (selectedItem?.id == null) {
      setOpenDetail(false);
      return;
    }
    setFormInputs((fields) =>
      fields.map((data) => {
        if (selectedItem.id === data.id) {
          return {...data, ...values};
        }

        return data;
      }),
    );

    setOpenDetail(false);
  };

  const handleInputSelect = (
    input: Partial<KbInputExtended> & { placeholder?: string },
  ) => {
    const newInput: KbInputExtended = {
      type: input.type,
      id: randomId(),
      name: '',
      defaultValue: '',
      placeholder: input.placeholder,
      title: '',
      description: '',
      required: input.required ?? false,
      isEnum: input.isEnum ?? false,
      choices: [],
    };

    if (
      input.type === 'select' ||
      input.type === 'multi-select' ||
      input.type === 'checkboxes'
    ) {
      newInput.choices = [];
    }

    if (input.type === 'multi-select' || input.type === 'checkboxes') {
      newInput.defaultValue = [];
    }

    setFormInputs((fields) => [...fields, newInput]);

    setOpen(false);
  };

  return (
    <div>
      {formInputs.length > 0 && (
        <StyledList>
          {formInputs.map((item: KbInputExtended, index: number) => (
            <AppInputRow
              key={item.id}
              index={index}
              item={item}
              handleInputChange={handleInputChange}
              handleDescriptionChange={handleDescriptionChange}
              setSelectedItem={setSelectedItem}
              setOpenDetail={setOpenDetail}
              handleDeleteInput={handleDeleteInput}
              handleRequiredChange={handleRequiredChange}
              handleEnumChange={handleEnumChange}
              onRowReorder={onRowReorder}
              showEnumOption
            />
          ))}
        </StyledList>
      )}
      <AppInputSelector
        open={open}
        onSelect={handleInputSelect}
        onOpenChange={setOpen}
        excludes={['json', 'file']} // exclude json to prevent nested
      >
        <Button
          type="primary"
          size="small"
          shape="round"
          icon={<MdAdd size={18}/>}
          onClick={() => setOpen(!open)}
          ghost
        >
          {field.placeholder || 'Add'}
        </Button>
      </AppInputSelector>

      <AppRowOptions
        open={openDetail}
        onCancel={() => setOpenDetail(false)}
        onFinish={onFinishDetails}
        selectedItem={selectedItem}
        initialValues={selectedItem ? {...selectedItem} : undefined}
      />
    </div>
  );
};

export const INPUT_COMPONENTS: Record<string, (props: any) => ReactElement> = {
  text: InputText,
  slider_number: InputSliderNumber,
  select: InputSelect,
  textarea: InputTextarea,
  json: InputJson,
  schema: InputJson,
  switch: InputSwitch,
  repeater: InputRepeater,
};
