'use client';
import {useEffect, useRef, useState} from 'react';

import {Col, Row, Tooltip} from 'antd';
import {useDrag, useDrop} from 'react-dnd';
import {MdDelete, MdFormatListBulleted, MdOutlineDragIndicator, MdOutlineMoreVert,} from 'react-icons/md';
import {INPUT_TYPE_ICONS, REQUIRED_CONTACT_FIELDS} from '@unpod/constants';
import AppPopconfirm from '../../../antd/AppPopconfirm';
import {
  StyledActions,
  StyledButton,
  StyledCheckbox,
  StyledContainer,
  StyledDragHandle,
  StyledInput,
  StyledInputWrapper,
  StyledLabel,
} from './index.styled';
import {useIntl} from 'react-intl';

type SchemaInput = {
  id: string | number;
  type: string;
  name?: string;
  title?: string;
  placeholder?: string;
  description?: string;
  required?: boolean;
  [key: string]: any;
};

type InputRowProps = {
  item: SchemaInput;
  handleInputChange: (value: string, item: SchemaInput) => void;
  handleDescriptionChange: (value: string, item: SchemaInput) => void;
  setSelectedItem: (item: SchemaInput) => void;
  setOpenDetail: (open: boolean) => void;
  handleDeleteInput: (item: SchemaInput) => void;
  handleRequiredChange: (checked: boolean, item: SchemaInput) => void;
  onRowReorder: (dragIndex: number, hoverIndex: number) => void;
  contentType?: string;
  index: number;
};

const InputRow = ({
                    item,
                    handleInputChange,
                    handleDescriptionChange,
                    setSelectedItem,
                    setOpenDetail,
                    handleDeleteInput,
                    handleRequiredChange,
                    onRowReorder,
                    contentType,
                    index,
                  }: InputRowProps) => {
  const [openDelTooltip, setDelTooltip] = useState(false);
  const [inputVal, setInputVal] = useState('');
  const [description, setDescription] = useState('');
  const ref = useRef<HTMLDivElement | null>(null);
  const {formatMessage} = useIntl();

  useEffect(() => {
    if (item.title) setInputVal(item.title);
  }, [item.title]);

  useEffect(() => {
    if (item.description) setDescription(item.description);
  }, [item.description]);

  const [{isOver}, drop] = useDrop<
    { index: number },
    void,
    { isOver: boolean; canDrop: boolean }
  >({
    accept: 'row',
    drop: (dragItem) => {
      onRowReorder(dragItem.index, index);
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  });

  const [{isDragging}, drag] = useDrag<
    { index: number },
    void,
    { isDragging: boolean }
  >({
    type: 'row',
    item: () => {
      return {index};
    },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const opacity = isDragging ? 0.05 : 1;
  drag(drop(ref));

  return (
    <StyledContainer isOver={isOver} style={{opacity}}>
      <StyledDragHandle ref={ref}>
        <MdOutlineDragIndicator fontSize={18}/>
      </StyledDragHandle>

      <Row gutter={[12, 12]}>
        <Col xs={24} sm={10}>
          <StyledInputWrapper>
            <StyledLabel>
              {formatMessage({id: 'knowledgeBase.parameter'})}:{' '}
            </StyledLabel>
            <StyledInput
              variant="filled"
              placeholder={item.title || item.placeholder}
              prefix={INPUT_TYPE_ICONS[item?.type || '']}
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onBlur={() => {
                if (inputVal !== item.title) handleInputChange(inputVal, item);
              }}
            />
          </StyledInputWrapper>
        </Col>

        <Col xs={24} sm={9}>
          <StyledInputWrapper>
            <StyledLabel>
              {formatMessage({id: 'form.description'})}:{' '}
            </StyledLabel>
            <StyledInput
              variant="filled"
              placeholder={formatMessage({id: 'form.description'})}
              defaultValue={item.description}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={() => {
                if (description !== item.description)
                  handleDescriptionChange(description, item);
              }}
            />
          </StyledInputWrapper>
        </Col>

        <Col xs={24} sm={5}>
          <StyledInputWrapper>
            <StyledLabel>{formatMessage({id: 'task.actions'})}:</StyledLabel>

            <StyledActions>
              {(item.type === 'select' ||
                item.type === 'multi-select' ||
                item.type === 'checkboxes') && (
                <Tooltip title="Choices">
                  <StyledButton
                    type="text"
                    size="small"
                    onClick={() => {
                      setSelectedItem(item);
                      setOpenDetail(true);
                    }}
                  >
                    <MdFormatListBulleted fontSize={18}/>
                  </StyledButton>
                </Tooltip>
              )}

              {(!REQUIRED_CONTACT_FIELDS.includes(item.name as any) ||
                contentType !== 'contact') && (
                <AppPopconfirm
                  title={formatMessage({
                    id: 'schema.deleteInput',
                  })}
                  description={formatMessage({
                    id: 'schema.deleteInputConfirm',
                  })}
                  onConfirm={() => handleDeleteInput(item)}
                  okText={formatMessage({id: 'common.yes'})}
                  cancelText={formatMessage({id: 'common.no'})}
                  onOpenChange={(open: boolean) => setDelTooltip(!open)}
                >
                  <Tooltip
                    title={formatMessage({id: 'common.delete'})}
                    open={openDelTooltip}
                    onOpenChange={(open: boolean) => setDelTooltip(open)}
                  >
                    <StyledButton type="text" size="small">
                      <MdDelete fontSize={18}/>
                    </StyledButton>
                  </Tooltip>
                </AppPopconfirm>
              )}

              <Tooltip title={formatMessage({id: 'common.required'})}>
                <StyledCheckbox
                  checked={item.required}
                  onChange={(e) => handleRequiredChange(e.target.checked, item)}
                />
              </Tooltip>

              <Tooltip
                title={formatMessage({id: 'common.moreInfo'})}
                placement="topLeft"
              >
                <StyledButton
                  type="text"
                  size="small"
                  onClick={() => {
                    setSelectedItem(item);
                    setOpenDetail(true);
                  }}
                >
                  <MdOutlineMoreVert fontSize={18}/>
                </StyledButton>
              </Tooltip>
            </StyledActions>
          </StyledInputWrapper>
        </Col>
      </Row>
    </StyledContainer>
  );
};

export default InputRow;
