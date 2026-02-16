import { memo } from 'react';

import { Button, Tooltip, Typography } from 'antd';
import { MdClose } from 'react-icons/md';
import { BsArrowReturnLeft } from 'react-icons/bs';
import { StyledParent, StyledTooltipContent } from './index.styled';

const { Paragraph } = Typography;

const ContextView = ({
  context,
  onContextClose,
}: {
  context: { description?: string; viewHtmlData?: string };
  onContextClose?: () => void;
}) => {
  return (
    <StyledParent>
      <BsArrowReturnLeft fontSize={16} />

      <Paragraph
        type="secondary"
        style={{ cursor: 'pointer' }}
        ellipsis={{
          tooltip: {
            placement: 'right',
            trigger: 'click',
            arrow: false,
            title: (
              <StyledTooltipContent>
                {context.viewHtmlData}
              </StyledTooltipContent>
            ),
            styles: {
              root: {
                maxWidth: 760,
              },
              container: {
                maxHeight: '70vh',
                overflowY: 'auto',
                padding: 0,
              },
            },
          },
        }}
      >
        {context.description}
      </Paragraph>

      <Tooltip title="Clear">
        <Button
          type="text"
          shape="circle"
          size="small"
          icon={<MdClose fontSize={16} />}
          onClick={onContextClose}
        />
      </Tooltip>
    </StyledParent>
  );
};

export default memo(ContextView);
