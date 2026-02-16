import React from 'react';
import PropTypes from 'prop-types';
import { Typography } from 'antd';
import { MdEdit } from 'react-icons/md';
import { RiVideoAddLine } from 'react-icons/ri';
import {
  StyledContainer,
  StyledContent,
  StyledItemRoot,
  StyledRoot,
  StyledTitleWrapper,
} from './index.styled';

const items = [
  {
    key: 'write',
    title: 'Write',
    icon: <MdEdit size={24} />,
    description: 'Create a new note',
  },
  {
    key: 'upload',
    title: 'Upload',
    icon: <RiVideoAddLine size={24} />,
    description: 'Audio, Video file',
  },
];

const { Paragraph, Title } = Typography;

const AddNote = ({ onAddClick }) => {
  const handleItemClick = (key) => {
    onAddClick?.(key);
  };

  return (
    <StyledRoot>
      <StyledContainer>
        {items.map((item) => (
          <StyledItemRoot
            key={item.key}
            onClick={() => handleItemClick(item.key)}
          >
            <StyledContent>
              <StyledTitleWrapper>
                {item.icon}
                <Title level={4}>{item.title}</Title>
              </StyledTitleWrapper>
              <Paragraph className="mb-0">{item.description}</Paragraph>
            </StyledContent>
          </StyledItemRoot>
        ))}
      </StyledContainer>
    </StyledRoot>
  );
};

const { func } = PropTypes;

AddNote.propTypes = {
  onAddClick: func,
};

export default AddNote;
