import React from 'react';
import type {PopoverProps} from 'antd';
import {Popover} from 'antd';

const AppPopover: React.FC<PopoverProps> = ({
                                              content,
                                              onOpenChange,
                                              trigger = ['click'],
                                              placement = 'bottomLeft',
                                              ...props
                                            }) => {
  return (
    <Popover
      content={content}
      styles={{
        content: {
          // padding: 12,
          borderRadius: 12,
        },
      }}
      placement={placement}
      trigger={trigger}
      onOpenChange={onOpenChange}
      {...props}
    />
  );
};

export default AppPopover;
