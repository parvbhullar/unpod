import {Checkbox, Flex, Typography} from 'antd';
import clsx from 'clsx';
import {useAppSpaceActionsContext, useAppSpaceContext,} from '@unpod/providers';
import {StyledInnerRoot, StyledItem, StyledListHeader, StyledMeta, StyledParagraph, StyledRoot,} from './index.styled';
import {IoCallOutline} from 'react-icons/io5';
import UserAvatar from '@unpod/components/common/UserAvatar';

const {Title} = Typography;

const DocItem = ({data}: { data: any }) => {
  const {setSelectedDocs} = useAppSpaceActionsContext();
  const {selectedDocs} = useAppSpaceContext();

  const onClick = () => {
    setSelectedDocs((prev: any[]) => {
      if (prev.includes(data.document_id)) {
        return prev.filter((item: any) => item !== data.document_id);
      } else {
        return [...prev, data.document_id];
      }
    });
  };
  return (
    <>
      <StyledRoot
        className={clsx('email-item', {
          // active: activeDocument?.document_id === data.document_id,
          // selected: selectedDocs.includes(data.document_id),
        })}
        onClick={onClick}
      >
        <StyledItem>
          <UserAvatar user={{full_name: data.name}} size={36}/>
        </StyledItem>

        <StyledInnerRoot>
          <StyledListHeader>
            <StyledMeta>
              <Title
                level={5}
                className={clsx({
                  'font-weight-normal': data.seen,
                })}
                ellipsis
              >
                {data.name}
              </Title>
            </StyledMeta>
            <Checkbox checked={selectedDocs.includes(data.document_id)}/>
          </StyledListHeader>

          {data.name && (
            <Flex align="center" gap={4} style={{marginTop: -6}}>
              <IoCallOutline size={12}/>
              <StyledParagraph type="secondary" className="mb-0" ellipsis>
                {data.title}
              </StyledParagraph>
            </Flex>
          )}
        </StyledInnerRoot>
      </StyledRoot>
    </>
  );
};

export default DocItem;
