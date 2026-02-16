import React, { useState } from 'react';
import { Button, Flex, Typography } from 'antd';
import { MdVisibility, MdVisibilityOff } from 'react-icons/md';
import AppCopyToClipboard from '@unpod/components/third-party/AppCopyToClipboard';

const { Text } = Typography;

type ApiKeyCellProps = {
  keyValue: string;
};

const ApiKeyCell: React.FC<ApiKeyCellProps> = ({ keyValue }) => {
  const [show, setShow] = useState(false);

  const masked = keyValue.replace(/.*/g, '*'.repeat(8));

  return (
    <Flex align="center" justify="space-between">
      <Text strong>{show ? keyValue : masked}</Text>

      <Flex align="center">
        <Button
          type="text"
          onClick={() => setShow(!show)}
          icon={
            show ? <MdVisibility size={18} /> : <MdVisibilityOff size={18} />
          }
        />
        <AppCopyToClipboard text={keyValue} showToolTip title="" />
      </Flex>
    </Flex>
  );
};

export default ApiKeyCell;
