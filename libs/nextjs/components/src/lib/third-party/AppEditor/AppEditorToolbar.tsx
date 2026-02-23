import React from 'react';
import PropTypes from 'prop-types';
import ToolbarFormats from './ToolbarOptions';
import {StyledToolbar} from './AppEditorInput/index.styled';
import {Tooltip} from 'antd';

const toolbarSelectBox = (formatData) => {
  const {className, options} = formatData;
  return (
    <select className={`ql-${className}`} onChange={(e) => e.persist()}>
      {options.map((value, index) => {
        return <option value={value} key={'option-' + index}/>;
      })}
      <option selected/>
    </select>
  );
};
const toolbarButton = (formatData) => {
  const {className, value, tooltip} = formatData;
  return (
    <Tooltip title={tooltip}>
      <button className={`ql-${className}`} value={value}/>
    </Tooltip>
  );
};
const AppEditorToolbar = ({toolbarId}) => {
  return (
    <StyledToolbar id={toolbarId}>
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
  );
};
AppEditorToolbar.propTypes = {
  toolbarId: PropTypes.string,
};
AppEditorToolbar.defaultProps = {
  toolbarId: 'toolbar',
};

export default AppEditorToolbar;
