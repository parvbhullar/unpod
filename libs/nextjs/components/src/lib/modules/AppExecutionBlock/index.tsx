import type {ReactNode} from 'react';
import {Fragment, useState} from 'react';

import {Button, Space, Typography} from 'antd';
import {MdCheck, MdClose, MdOutlineMoreHoriz} from 'react-icons/md';
import {StyledCollapse, StyledErrorButton, StyledSuccessButton, StyledWarningButton,} from './index.styled';
import DataTable from './DataTable';
import AppDrawer from '../../antd/AppDrawer';
import {useIntl} from 'react-intl';

const {Text, Paragraph} = Typography;

type AppExecutionBlockProps = {
  id: string | number;
  title: string;
  status?: 'success' | 'error' | 'pending' | 'progress' | 'warning';
  content?: ReactNode;
  threadId?: string;
  superbookHandle?: string;
  [key: string]: any;
};

const AppExecutionBlock = ({
                             id,
                             title,
                             status,
                             content,
                             threadId,
                             superbookHandle,
                             ...restProps
                           }: AppExecutionBlockProps) => {
  const {formatMessage} = useIntl();
  const [open, setOpen] = useState(false);

  return (
    <Fragment>
      <StyledCollapse
        key={id}
        items={[
          {
            key: id,
            label: (
              <Text
                type={
                  status === 'error'
                    ? 'danger'
                    : status === 'progress'
                      ? 'warning'
                      : undefined
                }
              >
                {title}
              </Text>
            ),
            extra: (
              <Space>
                <Button
                  type="text"
                  shape="round"
                  size="small"
                  onClick={(event) => {
                    event.stopPropagation();
                    setOpen(true);
                  }}
                >
                  {formatMessage({id: 'common.view'})}
                </Button>

                {status === 'success' && (
                  <StyledSuccessButton
                    type="primary"
                    shape="circle"
                    size="small"
                    icon={<MdCheck fontSize={18}/>}
                  />
                )}

                {status === 'error' && (
                  <StyledErrorButton
                    type="primary"
                    shape="circle"
                    size="small"
                    icon={<MdClose fontSize={18}/>}
                  />
                )}

                {status === 'warning' && (
                  <StyledWarningButton
                    type="primary"
                    shape="circle"
                    size="small"
                    icon={<MdOutlineMoreHoriz fontSize={18}/>}
                  />
                )}
              </Space>
            ),
            children: <Paragraph>{content}</Paragraph>,
            showArrow: false,
          },
        ]}
        defaultActiveKey={[]}
        bordered={false}
        {...restProps}
      />

      <AppDrawer
        // title="User Data"
        closeIcon={false}
        width="1050"
        open={open}
        onClose={() => setOpen(false)}
      >
        <DataTable threadId={threadId} superbookHandle={superbookHandle}/>
      </AppDrawer>
    </Fragment>
  );
};

export default AppExecutionBlock;
