import React, {useEffect} from 'react';
import {message, Space} from 'antd';
import {AiOutlineCloseCircle} from 'react-icons/ai';

export const Toast = ({
                        id,
                        title,
                        description = '',
                        close = true,
                        open,
                        duration = 6,
                        onOpenChange,
                        icon,
                        variant = 'info',
                      }) => {
  useEffect(() => {
    const config = {
      key: id,
      type: variant,
      icon: icon,
      content: (
        <Space>
          <span
            style={{
              marginLeft: 8,
              display: 'flex',
              flexDirection: 'column',
              textAlign: 'left',
            }}
          >
            <h3
              style={{
                margin: 0,
              }}
            >
              {title}
            </h3>
            <p
              style={{
                margin: 0,
              }}
            >
              {description}
            </p>
          </span>
          <div
            style={{
              cursor: 'pointer',
            }}
            onClick={() => {
              onOpenChange();
              message.destroy(id);
            }}
          >
            <AiOutlineCloseCircle fontSize={22}/>
          </div>
        </Space>
      ),
      duration: duration,
      onClose: onOpenChange,
    };
    message.open(config);
  }, [id]);
  return null;
};
