import React from 'react';
import PropTypes from 'prop-types';
import { Button, Result } from 'antd';
import { useIntl } from 'react-intl';

const SuccessResult = ({ onCloseClick, ...restProps }) => {
  const {formatMessage} = useIntl();

  return (
    <Result
      status="success"
      extra={[
        <Button type="primary" key="close" onClick={onCloseClick}>
          {formatMessage({ id: 'common.close' })}
        </Button>,
      ]}
      {...restProps}
    />
  );
};

SuccessResult.propTypes = {
  onCloseClick: PropTypes.func,
};

export default React.memo(SuccessResult);
