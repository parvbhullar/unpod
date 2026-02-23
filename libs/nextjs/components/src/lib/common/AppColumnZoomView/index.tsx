import {Button, Space, Tooltip, Typography} from 'antd';
import {MdArrowBack} from 'react-icons/md';
import clsx from 'clsx';
import AppMarkdownViewer from '../../third-party/AppMarkdownViewer';
import {isJson} from '@unpod/helpers/GlobalHelper';
import {
  StyledContentContainer,
  StyledContentWrapper,
  StyledCopyWrapper,
  StyledFullContent,
  StyledTitleContainer,
} from './index.styled';
import AppCopyToClipboard from '../../third-party/AppCopyToClipboard';
import AppJsonViewer from '../../third-party/AppJsonViewer';

const {Text} = Typography;

type ColumnZoomData = {
  title?: string;
  content?: string;
};

type AppColumnZoomViewProps = {
  showTitle?: boolean;
  selectedCol?: ColumnZoomData | null;
  onBackClick?: () => void;
};

const AppColumnZoomView: React.FC<AppColumnZoomViewProps> = ({
                                                               showTitle,
                                                               selectedCol,
                                                               onBackClick,
                                                             }) => {
  const isJsonContent = selectedCol?.content && isJson(selectedCol.content);

  return (
    <StyledFullContent className={clsx({open: selectedCol})}>
      {((showTitle && selectedCol?.title) || onBackClick) && (
        <StyledTitleContainer>
          <Space>
            {onBackClick && (
              <Tooltip title="Back">
                <Button
                  type="text"
                  size="small"
                  shape="circle"
                  onClick={onBackClick}
                >
                  <MdArrowBack fontSize={18}/>
                </Button>
              </Tooltip>
            )}

            {showTitle && selectedCol?.title && (
              <Text strong>{selectedCol?.title}</Text>
            )}
          </Space>
        </StyledTitleContainer>
      )}

      <StyledContentContainer
        className={clsx({'json-content': isJsonContent})}
      >
        <StyledCopyWrapper>
          <AppCopyToClipboard
            text={
              isJsonContent
                ? JSON.stringify(
                  JSON.parse(selectedCol?.content || ''),
                  null,
                  2,
                )
                : selectedCol?.content || ''
            }
            showToolTip
          />
        </StyledCopyWrapper>

        <StyledContentWrapper>
          {isJsonContent ? (
            <AppJsonViewer json={JSON.parse(selectedCol?.content || '')}/>
          ) : (
            <AppMarkdownViewer markdown={selectedCol?.content || ''}/>
          )}
        </StyledContentWrapper>
      </StyledContentContainer>
    </StyledFullContent>
  );
};

export default AppColumnZoomView;
