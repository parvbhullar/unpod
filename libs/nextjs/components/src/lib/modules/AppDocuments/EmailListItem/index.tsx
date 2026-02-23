import {Badge, Button, Space, Tooltip, Typography} from 'antd';
import {MdCheckBoxOutlineBlank, MdOutlineCheckBox} from 'react-icons/md';
import clsx from 'clsx';
import {changeDateStringFormat, getTimeFromNow,} from '@unpod/helpers/DateHelper';
import {getStringFromHtml} from '@unpod/helpers/GlobalHelper';
import UserAvatar from '../../../common/UserAvatar';
import {
  StyledHeaderExtra,
  StyledInnerRoot,
  StyledItem,
  StyledListHeader,
  StyledMeta,
  StyledRoot,
} from './index.styled';
import {useAppSpaceActionsContext, useAppSpaceContext,} from '@unpod/providers';
import {useRouter} from 'next/navigation';

const {Paragraph, Title, Text} = Typography;

type EmailDocument = {
  document_id: string;
  title: string;
  description?: string;
  seen?: boolean;
  date: string;
  user?: { name?: string };
  [key: string]: any;
};

type EmailListItemProps = {
  data: EmailDocument;
  showTimeFrom?: boolean;
};

const EmailListItem = ({data, showTimeFrom}: EmailListItemProps) => {
  const {setActiveDocument, setBreadcrumb, setActiveTab, setSelectedDocs} =
    useAppSpaceActionsContext();
  const {currentSpace, activeDocument, activeTab, selectedDocs} =
    useAppSpaceContext();
  const allowSelection = activeTab === 'logs';
  const router = useRouter();

  const onDocumentClick = (doc: EmailDocument) => {
    if (!currentSpace?.slug) return;
    if (!activeDocument) setActiveTab('knowledge');
    setActiveDocument(doc);
    setBreadcrumb(doc.title);
    router.replace(
      `/spaces/${currentSpace.slug}/${activeTab}/${doc.document_id}`,
    );
  };

  const onEmailToggleSelect = () => {
    setSelectedDocs((prev: any[]) => {
      if (prev.includes(data.document_id)) {
        return prev.filter((item) => item !== data.document_id);
      } else {
        return [...prev, data.document_id];
      }
    });
  };

  const onClick = () => {
    if (allowSelection) {
      onEmailToggleSelect();
    } else {
      onDocumentClick(data);
    }
  };

  return (
    <StyledRoot
      className={clsx('email-item', {
        active:
          !allowSelection && activeDocument?.document_id === data.document_id,
        selected: allowSelection && selectedDocs.includes(data.document_id),
      })}
      onClick={onClick}
    >
      <StyledItem>
        <UserAvatar user={{full_name: data?.user?.name}}/>
      </StyledItem>

      <StyledInnerRoot>
        <StyledListHeader>
          <StyledMeta>
            <Title
              level={5}
              className={clsx({'font-weight-normal': data.seen})}
              ellipsis
            >
              {data.title}
            </Title>
          </StyledMeta>

          <StyledHeaderExtra>
            <Space>
              {data.seen ? null : <Badge color="#796cff"/>}

              <Tooltip
                title={changeDateStringFormat(
                  data.date,
                  'YYYY-MM-DD HH:mm:ss',
                  'hh:mm A . DD MMM, YYYY',
                )}
              >
                <Text type="secondary">
                  {showTimeFrom
                    ? getTimeFromNow(data.date)
                    : changeDateStringFormat(
                      data.date,
                      'YYYY-MM-DD HH:mm:ss',
                      'DD MMM',
                    )}
                </Text>
              </Tooltip>
            </Space>

            {allowSelection && (
              <Button
                type={'text'}
                shape="circle"
                size="small"
                icon={
                  selectedDocs.includes(data.document_id) ? (
                    <MdOutlineCheckBox fontSize={21}/>
                  ) : (
                    <MdCheckBoxOutlineBlank fontSize={21}/>
                  )
                }
              />
            )}
          </StyledHeaderExtra>
        </StyledListHeader>

        {data.description && (
          <Paragraph
            type="secondary"
            className="mb-0"
            style={{maxWidth: '90%'}}
            ellipsis
          >
            {getStringFromHtml(data.description)}
          </Paragraph>
        )}
      </StyledInnerRoot>
    </StyledRoot>
  );
};

export default EmailListItem;
