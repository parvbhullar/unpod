import { useEffect, useState } from 'react';
import {
  StyledActionIcon,
  StyledEditButton,
  StyledIconWrapper,
  StyledTitle,
  StyledTitleWrapper,
  TitleWrapper,
} from './index.styled';
import { Flex, Form, Input } from 'antd';
import { MdOutlineCheck, MdOutlineClose, MdOutlinePhone } from 'react-icons/md';
import { EditOutlined } from '@ant-design/icons';
import { useTheme } from 'styled-components';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';
import { useIntl } from 'react-intl';

type BridgeTitleProps = {
  sipBridge?: any;
  onSave: (status: any, cb: (savedData?: any) => void) => void;
  onCancel?: () => void;
};

const BridgeTitle = ({ sipBridge, onSave, onCancel }: BridgeTitleProps) => {
  const [title, setTitle] = useState(sipBridge?.name || '');
  const [editTitle, setEditTitle] = useState(!title);
  const theme = useTheme();
  const mobileScreen = useMediaQuery(MobileWidthQuery);
  const { formatMessage } = useIntl();

  useEffect(() => {
    setTitle(sipBridge?.name || '');
    setEditTitle(!sipBridge?.name);
  }, [sipBridge]);

  const handleOnSave = () => {
    if (sipBridge?.name === title) {
      return setEditTitle(false);
    }
    onSave(sipBridge?.status, (savedData) => {
      if (savedData) {
        setEditTitle(false);
      }
    });
  };

  const handleOnCancel = () => {
    setTitle(sipBridge?.name || '');
    setEditTitle(false);
    onCancel?.();
  };

  return (
    <Flex align="flex-start">
      {!editTitle && (
        <StyledIconWrapper>
          <MdOutlinePhone fontSize={mobileScreen ? 16 : 21} />
        </StyledIconWrapper>
      )}

      <StyledTitleWrapper>
        {editTitle ? (
          <>
            <Form.Item
              name="name"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'common.titleError' }),
                },
              ]}
            >
              <Input
                style={{
                  height: 36,
                  fontSize: mobileScreen ? 14 : 18,
                  fontWeight: 600,
                }}
                defaultValue={title}
                placeholder={formatMessage({ id: 'bridgeNew.placeholder' })}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </Form.Item>

            {sipBridge && (
              <>
                <StyledActionIcon onClick={handleOnSave}>
                  <MdOutlineCheck fontSize={21} />
                </StyledActionIcon>
                <StyledActionIcon
                  className="close-btn"
                  onClick={handleOnCancel}
                >
                  <MdOutlineClose fontSize={21} />
                </StyledActionIcon>
              </>
            )}
          </>
        ) : (
          <>
            <TitleWrapper>
              <StyledTitle
                level={3}
                ellipsis={{ tooltip: true }}
                style={{ fontWeight: 600 }}
              >
                {title}
              </StyledTitle>
            </TitleWrapper>
            <StyledEditButton
              type="text"
              color="primary"
              icon={
                <EditOutlined
                  style={{
                    fontSize: mobileScreen ? 15 : 21,
                    color: theme?.palette?.primary,
                  }}
                />
              }
              onClick={() => {
                setTitle(sipBridge?.name || '');
                setEditTitle(true);
              }}
            />
          </>
        )}
      </StyledTitleWrapper>
    </Flex>
  );
};

export default BridgeTitle;
