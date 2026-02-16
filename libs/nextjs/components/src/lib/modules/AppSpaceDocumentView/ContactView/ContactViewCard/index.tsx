
import { Descriptions } from 'antd';
import { StyledContainer } from './index.styled';
import {
  capitalizedAllWords,
  convertMachineNameToName,
} from '@unpod/helpers/StringHelper';
import { useMediaQuery } from 'react-responsive';
import { TabWidthQuery } from '@unpod/constants';
import type { SpaceSchema } from '@unpod/constants/types';

const { Item } = Descriptions;

type Contact = Record<string, any>;
const ContactViewCard = ({
  contact,
  spaceSchema,
}: {
  contact: Contact;
  spaceSchema: SpaceSchema;
}) => {
  const mobileScreen = useMediaQuery(TabWidthQuery);
  const properties = spaceSchema?.properties || {};

  return (
    <StyledContainer>
      <Descriptions
        column={mobileScreen ? 1 : 2}
        bordered
        size={mobileScreen ? 'small' : 'default'}
      >
        {Object.keys(properties).map((field, index) => {
          const input = properties[field];
          const title =
            input?.title ||
            capitalizedAllWords(convertMachineNameToName(field) || '');
          const description = Array.isArray(contact[field])
            ? contact[field].toString()
            : contact[field]; // TODO replace labels with tags from the contact
          return (
            <Item key={index} label={title}>
              {description || 'N/A'}
            </Item>
          );
        })}
      </Descriptions>
    </StyledContainer>
  );
};

export default ContactViewCard;
