import {useEffect, useState} from 'react';
import {AppTabs} from '@unpod/components/antd';
import AppKbSchemaManager from '@unpod/components/modules/AppKbSchemaManager';
import {useAppSpaceActionsContext, useAppSpaceContext,} from '@unpod/providers';
import type {KbInput} from '@unpod/helpers/AppKbHelper';
import {getKbInputsStructure} from '@unpod/helpers/AppKbHelper';
import Edit from './Edit';
import ConfigureAgentModal from '../ConfigureAgent';
import {StyledTabWrapper} from '../index.styled';
import {useIntl} from 'react-intl';

type SchemaInput = KbInput & { [key: string]: unknown };

type EditSpaceProps = {
  onClose: (open: boolean) => void;
};

const EditSpace = ({onClose}: EditSpaceProps) => {
  const {spaceSchema, currentSpace} = useAppSpaceContext();
  const {setSpaceSchema, setCurrentSpace} = useAppSpaceActionsContext();
  const {formatMessage} = useIntl();
  const [inputs, setInputs] = useState<SchemaInput[]>([]);
  const [activeTab, setActiveTab] = useState('edit_space');

  useEffect(() => {
    if (spaceSchema) {
      const formInputs = getKbInputsStructure(spaceSchema);
      setInputs(formInputs as SchemaInput[]);
    }
  }, [spaceSchema]);

  const items = [
    {
      key: 'edit_space',
      label: formatMessage({id: 'space.basicInfo'}),
      children: (
        <Edit
          $bodyHeight={175}
          currentSpace={currentSpace}
          setCurrentSpace={setCurrentSpace}
          onClose={() => onClose(false)}
        />
      ),
    },
  ];

  if (currentSpace?.content_type === 'contact') {
    items.push({
      key: 'edit_schema',
      label: formatMessage({id: 'space.tableSchema'}),
      children: (
        <AppKbSchemaManager
          $bodyHeight={175}
          inputs={inputs as any}
          setInputs={setInputs as any}
          currentKb={currentSpace}
          onClose={() => onClose(false)}
          setSpaceSchema={setSpaceSchema}
        />
      ),
    });
  }
  if (currentSpace?.content_type === 'contact') {
    items.push({
      key: 'link_agent',
      label: formatMessage({id: 'space.linkAgent'}),
      children: (
        <ConfigureAgentModal
          $bodyHeight={175}
          currentSpace={currentSpace}
          onClose={() => onClose(false)}
        />
      ),
    });
  }
  if (currentSpace?.content_type === 'contact') {
    return (
      <StyledTabWrapper>
        <AppTabs
          items={items}
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key)}
          style={{marginTop: '-1rem', marginBottom: '-1rem'}}
        />
      </StyledTabWrapper>
    );
  } else {
    return (
      <Edit
        $bodyHeight={175}
        currentSpace={currentSpace}
        setCurrentSpace={setCurrentSpace}
        onClose={() => onClose(false)}
      />
    );
  }
};

export default EditSpace;
