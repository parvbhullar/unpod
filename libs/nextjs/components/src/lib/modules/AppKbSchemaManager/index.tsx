'use client';
import type { Dispatch, SetStateAction } from 'react';
import { useCallback, useState } from 'react';

import { Button, Form, Modal, Space, Tooltip } from 'antd';
import { MdAdd } from 'react-icons/md';
import { TbJson } from 'react-icons/tb';
import AppCopyToClipboard from '../../third-party/AppCopyToClipboard';
import { getMachineName } from '@unpod/helpers/StringHelper';
import { putDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { randomId } from '@unpod/helpers/GlobalHelper';
import { generateKbSchema } from '@unpod/helpers/AppKbHelper';
import AppInputSelector from '../../antd/AppInputSelector';
import AppCodeEditor from '../../third-party/AppCodeEditor';
import ManageDetails from './ManageDetails';
import InputRow from './InputRow';
import {
  StyledCopyWrapper,
  StyledHeaderRow,
  StyledList,
  StyledSchemaBody,
} from './index.styled';
import { DrawerBody, DrawerFooter } from '../../antd';
import { useIntl } from 'react-intl';
import { Spaces } from '@unpod/constants/types';

const { Item } = Form;

type SchemaInput = {
  id: string | number;
  type: string;
  name?: string;
  title?: string;
  placeholder?: string;
  defaultValue?: any;
  description?: string;
  required?: boolean;
  choices?: any[];
  [key: string]: any;
};

type AppKbSchemaManagerProps = {
  title?: string;
  currentKb: Spaces | null;
  $bodyHeight?: number;
  inputs: SchemaInput[];
  setInputs: Dispatch<SetStateAction<SchemaInput[]>>;
  onClose?: () => void;
  setSpaceSchema?: (schema: any) => void;
};

const AppKbSchemaManager = ({
  title,
  currentKb,
  $bodyHeight,
  inputs,
  setInputs,
  onClose,
  setSpaceSchema,
}: AppKbSchemaManagerProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();

  const [inputModalOpen, setInputModalOpen] = useState(false);
  const [openDetail, setOpenDetail] = useState(false);
  const [openSchema, setOpenSchema] = useState(false);
  const [schemaJson, setSchemaJson] = useState('');
  const [selectedItem, setSelectedItem] = useState<SchemaInput | null>(null);

  const handleInputSelect = (input: Partial<SchemaInput>) => {
    const newInput: SchemaInput = {
      id: randomId(),
      type: input.type || 'text',
      name: '',
      title: '',
      placeholder: input.placeholder
        ? formatMessage({ id: input.placeholder })
        : '',
      defaultValue: '',
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

    setInputs((fields) => [...fields, newInput]);

    setInputModalOpen(false);
  };

  const handleInputChange = (newValue: string, item: SchemaInput) => {
    setInputs((fields) =>
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

  const handleDescriptionChange = (newValue: string, item: SchemaInput) => {
    setInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          data.description = newValue;
          return data;
        }

        return data;
      }),
    );
  };

  const handleRequiredChange = (checked: boolean, item: SchemaInput) => {
    setInputs((fields) =>
      fields.map((data) => {
        if (item.id === data.id) {
          data.required = checked;
          return data;
        }

        return data;
      }),
    );
  };

  const onFinishDetails = (values: Partial<SchemaInput>) => {
    setInputs((fields) =>
      fields.map((data) => {
        if (selectedItem && selectedItem.id === data.id) {
          data = { ...data, ...values };
        }

        return data;
      }),
    );

    setOpenDetail(false);
  };

  const handleDeleteInput = (item: SchemaInput) => {
    setInputs((fields) => fields.filter((task) => item.id !== task.id));
  };

  const onViewSchemaJson = () => {
    const schema = generateKbSchema(inputs);
    setSchemaJson(JSON.stringify(schema, null, 2));

    setOpenSchema(true);
  };

  const onSaveClick = () => {
    const schema = generateKbSchema(inputs);
    setSpaceSchema?.(schema);

    putDataApi(`spaces/${currentKb?.slug}/`, infoViewActionsContext, { schema })
      .then((data: any) => {
        infoViewActionsContext.showMessage(data.message);
        onClose?.();
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const onRowReorder = useCallback((dragIndex: number, hoverIndex: number) => {
    setInputs((fields) => {
      const newItems = [...fields];
      const dragItem = fields[dragIndex];
      newItems.splice(dragIndex, 1);
      newItems.splice(hoverIndex, 0, dragItem);

      return newItems;
    });
  }, []);

  return (
    <>
      <DrawerBody bodyHeight={$bodyHeight} isTabDrawer={true}>
        <StyledHeaderRow>
          <Space>
            <AppInputSelector
              open={inputModalOpen}
              onSelect={handleInputSelect}
              onOpenChange={setInputModalOpen}
              allowFormInput
              placement="bottomRight"
            >
              <Button
                size="small"
                type="primary"
                ghost
                shape="round"
                icon={<MdAdd fontSize={16} />}
                onClick={() => setInputModalOpen(!inputModalOpen)}
              >
                {formatMessage({ id: 'common.addField' })}
              </Button>
            </AppInputSelector>

            <Tooltip
              title={formatMessage({ id: 'appKbSchema.viewSchemaJson' })}
            >
              <Button
                size="small"
                shape="round"
                type="primary"
                ghost
                onClick={onViewSchemaJson}
              >
                <TbJson fontSize={21} />
              </Button>
            </Tooltip>
          </Space>
        </StyledHeaderRow>

        <Item>
          {inputs.length > 0 && (
            <StyledList>
              {inputs.map((item, index) => (
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
                  contentType={currentKb?.content_type}
                />
              ))}
            </StyledList>
          )}
        </Item>
      </DrawerBody>

      <DrawerFooter>
        <Button onClick={onClose}>
          {formatMessage({ id: 'common.close' })}
        </Button>
        <Button type="primary" onClick={onSaveClick}>
          {formatMessage({ id: 'common.save' })}
        </Button>
      </DrawerFooter>

      <ManageDetails
        open={openDetail}
        onCancel={() => setOpenDetail(false)}
        onFinish={onFinishDetails}
        selectedItem={selectedItem}
        initialValues={selectedItem}
        contentType={currentKb?.content_type}
      />

      <Modal
        title={formatMessage({ id: 'appKbSchema.schemaTitle' })}
        open={openSchema}
        onCancel={() => setOpenSchema(false)}
        footer={null}
        centered
        width={680}
      >
        <StyledSchemaBody>
          <StyledCopyWrapper>
            <AppCopyToClipboard text={schemaJson} title="" />
          </StyledCopyWrapper>

          <AppCodeEditor
            placeholder={formatMessage({ id: 'appKbSchema.schemaPlaceholder' })}
            defaultValue={schemaJson}
            defaultLanguage="json"
            height={350}
          />
        </StyledSchemaBody>
      </Modal>
    </>
  );
};

export default AppKbSchemaManager;
