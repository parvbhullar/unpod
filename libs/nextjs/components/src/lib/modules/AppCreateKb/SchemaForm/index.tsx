import type {Dispatch, SetStateAction} from 'react';
import {useCallback, useState} from 'react';
import {MdAdd} from 'react-icons/md';
import AppInputSelector from '../../../antd/AppInputSelector';
import InputRow from '../../AppKbSchemaManager/InputRow';
import {getMachineName} from '@unpod/helpers/StringHelper';
import {randomId} from '@unpod/helpers/GlobalHelper';
import ManageDetails from '../../AppKbSchemaManager/ManageDetails';

import {Typography} from 'antd';
import {StyledList, StyledStickyButton} from '../index.styled';
import {useIntl} from 'react-intl';

const {Paragraph} = Typography;

export type SchemaInput = {
  id: string | number;
  type: string;
  name?: string;
  title?: string;
  description?: string;
  placeholder?: string;
  required?: boolean;
  choices?: any[];
  defaultValue?: any;
  [key: string]: any;
};

type SchemaFormProps = {
  formInputs: SchemaInput[];
  setFormInputs: Dispatch<SetStateAction<SchemaInput[]>>;
  contentType?: string;
};

const SchemaForm = ({
                      formInputs,
                      setFormInputs,
                      contentType,
                    }: SchemaFormProps) => {
  const [selectedItem, setSelectedItem] = useState<SchemaInput | null>(null);
  const [inputModalOpen, setInputModalOpen] = useState(false);
  const [openDetail, setOpenDetail] = useState(false);
  const {formatMessage} = useIntl();

  const handleDeleteInput = (item: SchemaInput) => {
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

  const handleRequiredChange = (checked: boolean, item: SchemaInput) => {
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          data.required = checked;
          return data;
        }

        return data;
      }),
    );
  };

  const handleDescriptionChange = (newValue: string, item: SchemaInput) => {
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          data.description = newValue;
          return data;
        }

        return data;
      }),
    );
  };

  const handleInputChange = (newValue: string, item: SchemaInput) => {
    setFormInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          data.title = newValue;
          if (newValue && !data.name) {
            data.name = getMachineName(newValue);
          }

          return data;
        }

        return data;
      }),
    );
  };

  const handleInputSelect = (input: Partial<SchemaInput>) => {
    const newInput: SchemaInput = {
      type: input.type || 'text',
      id: randomId(),
      name: '',
      defaultValue: '',
      placeholder: input.placeholder,
      title: '',
      description: '',
      required: input.required,
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

    setInputModalOpen(false);
  };

  const onFinishDetails = (values: Partial<SchemaInput>) => {
    setFormInputs((fields) =>
      fields.map((data) => {
        if (selectedItem && selectedItem.id === data.id) {
          data = {...data, ...values};
        }

        return data;
      }),
    );

    setOpenDetail(false);
  };

  return (
    <>
      <Paragraph strong>
        {formatMessage({id: 'knowledgeBase.addSchemaFields'})}
      </Paragraph>
      {formInputs.length > 0 && (
        <StyledList>
          {formInputs.map((item, index) => (
            <InputRow
              key={item.id}
              index={index}
              item={item}
              handleInputChange={handleInputChange}
              handleDescriptionChange={handleDescriptionChange}
              setSelectedItem={setSelectedItem}
              setOpenDetail={setOpenDetail}
              handleDeleteInput={handleDeleteInput}
              handleRequiredChange={handleRequiredChange}
              onRowReorder={onRowReorder}
              contentType={contentType}
            />
          ))}
        </StyledList>
      )}

      <AppInputSelector
        open={inputModalOpen}
        onSelect={handleInputSelect}
        onOpenChange={setInputModalOpen}
      >
        <StyledStickyButton
          type="primary"
          size="small"
          shape="round"
          onClick={() => setInputModalOpen(!inputModalOpen)}
          ghost
        >
          <MdAdd fontSize={16}/>
          <span>{formatMessage({id: 'common.addField'})}</span>
        </StyledStickyButton>
      </AppInputSelector>
      <ManageDetails
        open={openDetail}
        onCancel={() => setOpenDetail(false)}
        onFinish={onFinishDetails}
        selectedItem={selectedItem}
        initialValues={selectedItem}
        contentType={contentType}
      />
    </>
  );
};

export default SchemaForm;
