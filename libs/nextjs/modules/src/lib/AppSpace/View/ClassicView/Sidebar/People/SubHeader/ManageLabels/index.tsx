import {useState} from 'react';
import {Button, Space, Typography} from 'antd';
import {MdAdd, MdDeleteOutline, MdEdit} from 'react-icons/md';
import AddTagForm from './AddTagForm';
import {StyledContent, StyledTagContainer, StyledWrapper,} from './index.styled';
import {AppConfirmDeletePopover} from '@unpod/components/antd';
import {deleteDataApi, useInfoViewActionsContext} from '@unpod/providers';
import AppTabs from '@unpod/components/antd/AppTabs';
import {useIntl} from 'react-intl';

const {Title} = Typography;

type LabelTag = {
  slug?: string;
  name?: string;
};

type ManageLabelsProps = {
  labels: { default_tags?: LabelTag[]; object_tags?: LabelTag[] };
  currentSpace: { slug?: string };
  reCallAPI: () => void;
};

const ManageLabels = ({
                        labels,
                        currentSpace,
                        reCallAPI,
                      }: ManageLabelsProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {formatMessage} = useIntl();

  const [activeTab, setActiveTab] = useState('list');
  const [selectedTag, setSelectedTag] = useState<LabelTag | null>(null);

  const onTabChange = (key: string) => {
    setActiveTab(key);
    if (key === 'list') {
      setSelectedTag(null);
    }
  };

  const onAddTag = () => {
    setActiveTab('form');
    setSelectedTag(null);
  };

  const onEditTag = (tag: LabelTag) => {
    setSelectedTag(tag);
    setActiveTab('form');
  };

  const onDeleteTag = (tag: LabelTag) => {
    deleteDataApi(
      `core/relevant-tags/delete/`,
      infoViewActionsContext,
      {},
      {
        content_type_model: 'space',
        slug: currentSpace.slug,
        tag_slug: tag.slug,
      },
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        reCallAPI();
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const onTagSaved = () => {
    setActiveTab('list');
    setSelectedTag(null);
    reCallAPI();
  };

  // "tab.labels": "लेबल",
  //   "tab.editLabels": "लेबल संपादित करें",
  //   "tab.newLabels": "नया लेबल"

  return (
    <AppTabs
      items={[
        {
          key: 'list',
          label: formatMessage({id: 'tab.labels'}),
          children: activeTab === 'list' && (
            <StyledWrapper>
              {(labels.default_tags || []).map((tag) => (
                <StyledTagContainer key={tag.slug}>
                  <StyledContent>
                    <Title
                      level={5}
                      className="font-weight-normal mb-0"
                      ellipsis
                    >
                      {tag.name}
                    </Title>
                  </StyledContent>
                </StyledTagContainer>
              ))}

              {(labels.object_tags || []).map((tag) => (
                <StyledTagContainer key={tag.slug}>
                  <StyledContent>
                    <Title level={5} className="mb-0">
                      {tag.name}
                    </Title>
                  </StyledContent>

                  <Space size="small">
                    <Button
                      type="text"
                      size="small"
                      icon={<MdEdit fontSize={18}/>}
                      onClick={() => onEditTag(tag)}
                    />

                    <AppConfirmDeletePopover
                      title={formatMessage({id: 'manageLabels.delete'})}
                      message={formatMessage({id: 'manageLabels.message'})}
                      onConfirm={() => onDeleteTag(tag)}
                    >
                      <Button
                        type="text"
                        size="small"
                        shape="circle"
                        icon={<MdDeleteOutline fontSize={18}/>}
                      />
                    </AppConfirmDeletePopover>
                  </Space>
                </StyledTagContainer>
              ))}
            </StyledWrapper>
          ),
        },
        {
          key: 'form',
          label: selectedTag
            ? formatMessage({id: 'tab.editLabels'})
            : formatMessage({id: 'tab.newLabels'}),
          children: activeTab === 'form' && (
            <AddTagForm
              selectedTag={selectedTag}
              currentSpace={currentSpace}
              onTagSaved={onTagSaved}
            />
          ),
        },
      ]}
      activeKey={activeTab}
      onChange={onTabChange}
      style={{marginTop: -16}}
      tabBarExtraContent={
        activeTab === 'list' && (
          <Button
            size="small"
            type="primary"
            ghost
            shape="round"
            icon={<MdAdd fontSize={16}/>}
            onClick={onAddTag}
          >
            {formatMessage({id: 'manageLabels.add'})}
          </Button>
        )
      }
    />
  );
};

export default ManageLabels;
