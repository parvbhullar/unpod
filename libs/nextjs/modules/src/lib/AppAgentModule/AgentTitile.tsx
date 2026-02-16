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
import { MdOutlineCheck, MdOutlineClose } from 'react-icons/md';
import { EditOutlined } from '@ant-design/icons';
import { RiRobot2Line } from 'react-icons/ri';
import { useTheme } from 'styled-components';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';

type AgentTitleProps = {
  agentData?: any;
  onSave?: () => void;
  onClose?: () => void;
};

const AgentTitle = ({ agentData, onSave, onClose }: AgentTitleProps) => {
  const [title, setTitle] = useState(agentData?.name || '');
  const [editTitle, setEditTitle] = useState(!title);
  const theme = useTheme();
  const mobileScreen = useMediaQuery(MobileWidthQuery);

  useEffect(() => {
    setTitle(agentData?.name || '');
    setEditTitle(!agentData?.name);
  }, [agentData]);

  const handleOnSaveTitle = () => {
    if (agentData?.name === title) {
      return setEditTitle(false);
    }
    onSave?.();
    setEditTitle(false);
  };

  const handleOnClose = () => {
    setTitle(agentData?.name || '');
    setEditTitle(false);
    onClose?.();
  };

  return (
    <Flex align="start" gap={'small'}>
      {!editTitle && (
        <StyledIconWrapper>
          <RiRobot2Line fontSize={mobileScreen ? 16 : 21} />
        </StyledIconWrapper>
      )}
      <StyledTitleWrapper>
        {editTitle ? (
          <>
            <Form.Item
              name={'name'}
              rules={[
                {
                  required: true,
                  message: 'Title is required',
                },
              ]}
            >
              <Input
                style={{
                  height: 36,
                  fontSize: mobileScreen ? 14 : 18,
                  fontWeight: 600,
                }}
                className="title-input"
                placeholder="Enter title..."
                value={title}
                defaultValue={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </Form.Item>
            {agentData?.handle && (
              <>
                <StyledActionIcon onClick={handleOnSaveTitle}>
                  <MdOutlineCheck fontSize={21} />
                </StyledActionIcon>
                <StyledActionIcon className="close-btn" onClick={handleOnClose}>
                  <MdOutlineClose fontSize={21} />
                </StyledActionIcon>
              </>
            )}
          </>
        ) : (
          <>
            <TitleWrapper>
              <StyledTitle level={3} ellipsis={{ tooltip: true }}>
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
              onClick={() => setEditTitle(true)}
            />
          </>
        )}
      </StyledTitleWrapper>
    </Flex>
  );
};

export default AgentTitle;
