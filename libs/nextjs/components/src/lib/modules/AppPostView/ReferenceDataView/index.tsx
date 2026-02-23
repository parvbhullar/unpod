import {memo} from 'react';

import {getStringFromHtml} from '@unpod/helpers/GlobalHelper';
import {BsArrowReturnLeft} from 'react-icons/bs';
import {RxExternalLink} from 'react-icons/rx';
import {Button, Typography} from 'antd';
import {getDataApi, useInfoViewActionsContext} from '@unpod/providers';
import {downloadFile} from '@unpod/helpers/FileHelper';
import {StyledContainer, StyledParent} from './index.styled';

const {Paragraph} = Typography;

const ReferenceDataView = ({post}: { post?: any }) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {data, execution_type} = post?.related_data || {};

  const onViewClick = () => {
    if (data.meta?.source_url || data.meta?.siteUrl) {
      const newWindow = window.open(
        data.meta?.source_url || data.meta?.siteUrl,
        '_blank',
      );
      newWindow?.focus();
    } else {
      getDataApi('media/pre-signed-url/', infoViewActionsContext, {
        url: data.url,
      })
        .then((res: any) => {
          downloadFile(res.data.url);
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    }
  };

  return (
    data &&
    data.content && (
      <StyledContainer>
        <StyledParent>
          <BsArrowReturnLeft fontSize={16}/>
          <Paragraph type="secondary" ellipsis={{rows: 1}}>
            {getStringFromHtml(data.content)}
          </Paragraph>

          {execution_type === 'general' && (
            <Button
              type="text"
              size="small"
              shape="circle"
              onClick={onViewClick}
            >
              <RxExternalLink fontSize={16}/>
            </Button>
          )}
        </StyledParent>
      </StyledContainer>
    )
  );
};

export default memo(ReferenceDataView);
