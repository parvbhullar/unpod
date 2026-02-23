'use client';
import React, {useEffect, useRef, useState} from 'react';
import {Col, Row, Tooltip} from 'antd';
import {useDrag, useDrop} from 'react-dnd';
import {MdDelete, MdFormatListBulleted, MdOutlineDragIndicator, MdOutlineMoreVert,} from 'react-icons/md';
import {INPUT_TYPE_ICONS, REQUIRED_CONTACT_FIELDS} from '@unpod/constants';
import AppPopconfirm from '../../antd/AppPopconfirm';
import {
  StyledActions,
  StyledActionsWrapper,
  StyledButton,
  StyledCheckbox,
  StyledContainer,
  StyledDragHandle,
  StyledInput,
  StyledInputWrapper,
  StyledLabel,
  StyledRoot,
  StyledRowContainer,
} from './index.styled';

type InputItem = {
  title?: string;
  name?: string;
  type?: string;
  placeholder?: string;
  description?: string;
  required?: boolean;
  isEnum?: boolean;
};

type AppInputRowProps = {
  item: InputItem;
  handleInputChange?: (value: string, item: InputItem) => void;
  handleDescriptionChange?: (value: string, item: InputItem) => void;
  setSelectedItem?: (item: InputItem) => void;
  setOpenDetail?: (open: boolean) => void;
  handleDeleteInput?: (item: InputItem) => void;
  handleRequiredChange?: (checked: boolean, item: InputItem) => void;
  handleEnumChange?: (checked: boolean, item: InputItem) => void;
  onRowReorder?: (fromIndex: number, toIndex: number) => void;
  contentType?: string;
  showEnumOption?: boolean;
  index?: number;
};

const AppInputRow: React.FC<AppInputRowProps> = ({
                                                   item,
                                                   handleInputChange,
                                                   handleDescriptionChange,
                                                   setSelectedItem,
                                                   setOpenDetail,
                                                   handleDeleteInput,
                                                   handleRequiredChange,
                                                   handleEnumChange,
                                                   onRowReorder,
                                                   contentType,
                                                   showEnumOption,
                                                   index = 0,
                                                 }) => {
  const [openDelTooltip, setDelTooltip] = useState(false);
  const [inputVal, setInputVal] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const ref = useRef<HTMLDivElement | null>(null);
  const isRequiredContactField =
    !!item.name &&
    (REQUIRED_CONTACT_FIELDS as readonly string[]).includes(item.name);

  useEffect(() => {
    if (item.title) setInputVal(item.title);
  }, [item.title]);

  useEffect(() => {
    if (item.description) setDescription(item.description);
  }, [item.description]);

  const [{isOver}, drop] = useDrop<
    { index: number },
    void,
    { isOver: boolean }
  >({
    accept: 'row',
    drop: (dragItem) => {
      if (onRowReorder) {
        onRowReorder(dragItem.index, index);
      }
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
    <StyledRoot isOver={isOver} style={{opacity}}>
      <StyledDragHandle ref={ref}>
        <MdOutlineDragIndicator fontSize={18}/>
      </StyledDragHandle>

      <StyledContainer>
        <StyledRowContainer>
          <Row gutter={[12, 12]}>
            <Col sm={24} md={12}>
              <StyledInputWrapper>
                <StyledLabel>Parameter: </StyledLabel>
                <StyledInput
                  variant="filled"
                  placeholder={item.title || item.placeholder}
                  prefix={item.type ? INPUT_TYPE_ICONS[item.type] : undefined}
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  onBlur={() => {
                    if (inputVal !== item.title) {
                      handleInputChange?.(inputVal, item);
                    }
                  }}
                />
              </StyledInputWrapper>
            </Col>

            <Col sm={24} md={12}>
              <StyledInputWrapper>
                <StyledLabel>Description: </StyledLabel>
                <StyledInput
                  variant="filled"
                  placeholder="Description"
                  defaultValue={item.description}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  onBlur={() => {
                    if (description !== item.description) {
                      handleDescriptionChange?.(description, item);
                    }
                  }}
                />
              </StyledInputWrapper>
            </Col>
          </Row>
        </StyledRowContainer>

        <StyledActionsWrapper>
          <StyledLabel>Actions:</StyledLabel>

          <StyledActions>
            {(item.type === 'select' ||
                item.type === 'multi-select' ||
                item.type === 'checkboxes') &&
              !showEnumOption && (
                <Tooltip title="Choices">
                  <StyledButton
                    type="text"
                    size="small"
                    onClick={() => {
                      setSelectedItem?.(item);
                      setOpenDetail?.(true);
                    }}
                  >
                    <MdFormatListBulleted fontSize={18}/>
                  </StyledButton>
                </Tooltip>
              )}

            {showEnumOption && item.type === 'text' && (
              <StyledCheckbox
                checked={item.isEnum}
                onChange={(e) => handleEnumChange?.(e.target.checked, item)}
              >
                Enum
              </StyledCheckbox>
            )}

            {(!isRequiredContactField || contentType !== 'contact') && (
              <AppPopconfirm
                title="Delete input"
                description="Are you sure to delete this input?"
                onConfirm={() => handleDeleteInput?.(item)}
                okText="Yes"
                cancelText="No"
                onOpenChange={(open: boolean) => setDelTooltip(!open)}
              >
                <Tooltip
                  title="Delete"
                  open={openDelTooltip}
                  onOpenChange={(open: boolean) => setDelTooltip(open)}
                >
                  <StyledButton type="text" size="small">
                    <MdDelete fontSize={18}/>
                  </StyledButton>
                </Tooltip>
              </AppPopconfirm>
            )}

            <Tooltip title="Required">
              <StyledCheckbox
                checked={item.required}
                onChange={(e) => handleRequiredChange?.(e.target.checked, item)}
              />
            </Tooltip>

            <Tooltip title="More Info">
              <StyledButton
                // type="text"
                size="small"
                onClick={() => {
                  setSelectedItem?.(item);
                  setOpenDetail?.(true);
                }}
              >
                <MdOutlineMoreVert fontSize={16}/>
              </StyledButton>
            </Tooltip>
          </StyledActions>
        </StyledActionsWrapper>
      </StyledContainer>
    </StyledRoot>
  );
};

export default AppInputRow;
