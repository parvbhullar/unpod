'use client';
import {StyledAvatar, StyledDocumentsList, StyledRoot} from './index.styled';
import {MdCheck} from 'react-icons/md';
import {RxCross2} from 'react-icons/rx';
import ListItems from '../../Conversation/Overview/ListItems';
import {Typography} from 'antd';
import AppList from '@unpod/components/common/AppList';
import {RenderDescription} from './RenderDescription';
import {useAppSpaceContext} from '@unpod/providers';
import {useMediaQuery} from 'react-responsive';
import {MobileWidthQuery} from '@unpod/constants';

const {Text} = Typography;

const Tasks = () => {
  const {activeCall} = useAppSpaceContext();
  const activeCallAny = activeCall || {};
  const mobileScreen = useMediaQuery(MobileWidthQuery);

  const getStatusIcon = (status: any) => {
    if (status === 'failed') return <RxCross2 size={mobileScreen ? 16 : 20}/>;
    if (status === 'hold') return <RxCross2 size={mobileScreen ? 16 : 20}/>;
    return <MdCheck size={mobileScreen ? 16 : 20}/>;
  };

  const data =
    activeCallAny?.output?.post_call_data?.profile_summary?.questions_asked ||
    [];

  return (
    <StyledRoot>
      <StyledDocumentsList>
        <AppList
          data={data}
          itemSpacing={16}
          renderItem={(summary: any) => (
            <ListItems
              title={
                <Text
                  strong
                  className="text-capitalize"
                  style={{fontSize: 15, color: '#262626'}}
                >
                  {summary}
                </Text>
              }
              description={<RenderDescription item={activeCallAny}/>}
              avatar={
                <StyledAvatar
                  className={
                    activeCallAny.status === 'completed'
                      ? 'success'
                      : activeCallAny.status === 'failed'
                        ? 'error'
                        : ''
                  }
                  icon={getStatusIcon(activeCallAny.status)}
                  shape="square"
                  size={mobileScreen ? 40 : 48}
                />
              }
              $radius="12px"
              style={{
                padding: '16px',
                marginBottom: '12px',
                border: '1px solid #f0f0f0',
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                background: '#ffffff',
              }}
              onMouseEnter={(e: any) => {
                e.currentTarget.style.boxShadow =
                  '0 4px 12px rgba(0, 0, 0, 0.08)';
                e.currentTarget.style.borderColor = '#d9d9d9';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e: any) => {
                e.currentTarget.style.boxShadow = 'none';
                e.currentTarget.style.borderColor = '#f0f0f0';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            />
          )}
        />
      </StyledDocumentsList>
    </StyledRoot>
  );
};

export default Tasks;
