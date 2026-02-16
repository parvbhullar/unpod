import React from 'react';
import { Form, Tooltip } from 'antd';
import PropTypes from 'prop-types';
import { StyledAppScrollbar, StyledMailModalTextArea } from './index.styled';
import ToolbarFormats from './ToolbarOptions';
import { StyledToolbar } from './AppEditorInput/index.styled';
import AppEditorInput from './AppEditorInput';
import { useIntl } from 'react-intl';

const toolbarSelectBox = (formatData) => {
  const { className, options } = formatData;
  return (
    <select className={`ql-${className}`} onChange={(e) => e.persist()}>
      <option selected />
      {options.map((value, index) => {
        return <option value={value} key={'option-' + index} />;
      })}
    </select>
  );
};
const toolbarButton = (formatData) => {
  const { className, value, tooltip } = formatData;
  return (
    <Tooltip title={tooltip}>
      <button className={`ql-${className}`} value={value} />
    </Tooltip>
  );
};

const AppEditor = ({
  name,
  placeHolder,
  required,
  visible,
  children,
  value,
  ...restProps
}) => {
  const { formatMessage } = useIntl();

  return (
    <StyledMailModalTextArea className="app-editor">
      <StyledAppScrollbar visible={visible}>
        {children}
        <Form.Item
          name={name}
          rules={[
            {
              required: required,
              message: formatMessage({ id: 'validation.contentRequired' }),
            },
          ]}
          className="app-editor__form-item"
        >
          <AppEditorInput
            name={name}
            defaultValue={value}
            placeholder={
              placeHolder || formatMessage({ id: 'common.typeSomething' })
            }
            toolbarId="app-toolbar-container"
            theme="snow"
            noToolbar
            {...restProps}
          />
        </Form.Item>
      </StyledAppScrollbar>

      <StyledToolbar
        id="app-toolbar-container"
        className="theme-snow"
        style={{
          position: 'absolute',
          visibility: visible ? 'visible' : 'hidden',
          height: visible ? 'auto' : 0,
          padding: visible ? '8px' : 0,
          marginTop: visible ? '16px' : 0,
          width: '100%',
        }}
      >
        <span className="ql-formats">
          {ToolbarFormats.map((format, index) => (
            <React.Fragment key={index}>
              {format?.options
                ? toolbarSelectBox(format, index)
                : toolbarButton(format, index)}
            </React.Fragment>
          ))}
        </span>
      </StyledToolbar>
    </StyledMailModalTextArea>
  );
};

AppEditor.propTypes = {
  name: PropTypes.string,
  required: PropTypes.bool,
  visible: PropTypes.bool,
  placeHolder: PropTypes.string,
};

AppEditor.defaultProps = {
  name: 'content',
  required: false,
  visible: false,
  placeHolder: 'Enter your text here',
};
export default AppEditor;
