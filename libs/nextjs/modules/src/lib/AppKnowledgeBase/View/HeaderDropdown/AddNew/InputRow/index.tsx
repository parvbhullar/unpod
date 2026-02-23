import React, {useEffect, useRef, useState} from 'react';
import {Col, Row, Select, Tooltip} from 'antd';
import {useDrag, useDrop} from 'react-dnd';
import {MdDelete, MdFormatListBulleted, MdOutlineDragIndicator, MdOutlineMoreVert,} from 'react-icons/md';
import {AppPopconfirm} from '@unpod/components/antd';
import {
  StyledActions,
  StyledButton,
  StyledCheckbox,
  StyledContainer,
  StyledDatePicker,
  StyledDragHandle,
  StyledInput,
  StyledInputWrapper,
  StyledLabel,
  StyledSelect,
  StyledTimePicker,
} from './index.styled';
import {getDateObject} from '@unpod/helpers/DateHelper';
import {INPUT_TYPE_ICONS} from '@unpod/constants';
import {useIntl} from 'react-intl';

const {Option} = Select;

const PickerWithType = ({type, onChange, ...props}) => {
  if (type === 'time')
    return <StyledTimePicker onChange={onChange} {...props} />;
  if (type === 'date')
    return <StyledDatePicker onChange={onChange} {...props} />;
  return <StyledDatePicker onChange={onChange} {...props} showTime/>;
};

const InputRow = ({
                    item,
                    handleInputChange,
                    handleDefaultValueChange,
                    setSelectedItem,
                    setOpenDetail,
                    handleDeleteInput,
                    handleRequiredChange,
                    onRowReorder,
                    index,
                  }) => {
  const [openDelTooltip, setDelTooltip] = useState(false);
  const [inputVal, setInputVal] = useState(null);
  const [defaultVal, setDefaultVal] = useState(null);
  const ref = useRef(null);
  const {formatMessage} = useIntl();

  useEffect(() => {
    if (item.title) setInputVal(item.title);
  }, [item.title]);

  useEffect(() => {
    if (item.defaultValue) setDefaultVal(item.defaultValue);
  }, [item.defaultValue]);

  const [{isOver}, drop] = useDrop({
    accept: 'row',
    drop: (item) => {
      onRowReorder(item.index, index);
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  });

  const [{isDragging}, drag] = useDrag({
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
            <StyledLabel>Parameter: </StyledLabel>
            <StyledInput
              variant="filled"
              placeholder={item.title || item.placeholder}
              prefix={INPUT_TYPE_ICONS[item?.type]}
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
            <StyledLabel>Default value: </StyledLabel>

            {item.type === 'select' ||
            item.type === 'multi-select' ||
            item.type === 'checkboxes' ? (
              <StyledSelect
                variant="filled"
                placeholder={formatMessage({id: 'form.defaultValue'})}
                value={defaultVal}
                onChange={(value) => handleDefaultValueChange(value, item)}
                mode={
                  item.type === 'multi-select' || item.type === 'checkboxes'
                    ? 'multiple'
                    : ''
                }
              >
                {(item.choices || []).map((choice, index) => (
                  <Option key={index} value={choice}>
                    {choice}
                  </Option>
                ))}
              </StyledSelect>
            ) : item.type === 'date' ? (
              <PickerWithType
                variant="filled"
                placeholder={formatMessage({id: 'form.defaultValue'})}
                type={item.type}
                value={getDateObject(defaultVal, 'YYYY-MM-DD')}
                onChange={(value, dateString) => {
                  handleDefaultValueChange(dateString, item);
                }}
              />
            ) : item.type === 'time' ? (
              <PickerWithType
                variant="filled"
                placeholder={formatMessage({id: 'form.defaultValue'})}
                type={item.type}
                value={getDateObject(defaultVal, 'HH:mm:ss')}
                onChange={(value, dateString) => {
                  handleDefaultValueChange(dateString, item);
                }}
              />
            ) : item.type === 'datetime' ? (
              <PickerWithType
                variant="filled"
                placeholder={formatMessage({id: 'form.defaultValue'})}
                type={item.type}
                value={getDateObject(defaultVal, 'YYYY-MM-DD  HH:mm:ss')}
                onChange={(value, dateString) => {
                  handleDefaultValueChange(dateString, item);
                }}
              />
            ) : (
              <StyledInput
                variant="filled"
                placeholder={formatMessage({id: 'form.defaultValue'})}
                value={defaultVal}
                onChange={(e) => setDefaultVal(e.target.value)}
                onBlur={() => {
                  if (defaultVal !== item.title)
                    handleDefaultValueChange(defaultVal, item);
                }}
              />
            )}
          </StyledInputWrapper>
        </Col>

        <Col xs={24} sm={5}>
          <StyledInputWrapper>
            <StyledLabel>Actions:</StyledLabel>

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

              <AppPopconfirm
                title={formatMessage({id: 'schema.deleteInput'})}
                description={formatMessage({id: 'schema.deleteInputConfirm'})}
                onConfirm={() => handleDeleteInput(item)}
                okText={formatMessage({id: 'common.yes'})}
                cancelText={formatMessage({id: 'common.no'})}
                onOpenChange={(open) => setDelTooltip(!open)}
              >
                <Tooltip
                  title={formatMessage({id: 'common.delete'})}
                  open={openDelTooltip}
                  onOpenChange={(open) => setDelTooltip(open)}
                >
                  <StyledButton type="text" size="small">
                    <MdDelete fontSize={18}/>
                  </StyledButton>
                </Tooltip>
              </AppPopconfirm>

              <Tooltip title={formatMessage({id: 'common.required'})}>
                <StyledCheckbox
                  checked={item.required}
                  onChange={(e) => handleRequiredChange(e.target.checked, item)}
                />
              </Tooltip>

              <Tooltip title={formatMessage({id: 'common.moreInfo'})}>
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

const {object, func} = PropTypes;

InputRow.propTypes = {
  item: object,
  handleInputChange: func,
  handleDefaultValueChange: func,
  setSelectedItem: func,
  setOpenDetail: func,
  handleDeleteInput: func,
  handleRequiredChange: func,
};

export default InputRow;
