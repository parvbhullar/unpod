import { Fragment, useState } from 'react';
import AppMarkdownEditor from '@unpod/components/third-party/AppMarkdownEditor';
import {
  StyledContent,
  StyledPrimaryButton,
  StyledSecoundryButton,
} from './index.styled';
import { Flex, Form } from 'antd';
import {
  postDataApi,
  putDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';

const { Item } = Form;

const SummaryEditar = ({
  currentPost,
  setCurrentPost,
  setIsEditing,
  token,
}: {
  currentPost: any;
  setCurrentPost: (post: any) => void;
  setIsEditing: (value: boolean) => void;
  token: any;
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [localSummary, setLocalSummary] = useState(currentPost.content);

  const onDataSaved = (data: any) => {
    setCurrentPost(data);
  };

  const saveData = (payload: any) => {
    if (currentPost?.slug) {
      putDataApi(
        `threads/${currentPost.slug}/action/`,
        infoViewActionsContext,
        payload,
      )
        .then((response: any) => {
          infoViewActionsContext.showMessage(response.message);
          onDataSaved(response.data);
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    } else {
      const requestUrl = `threads/${token}/`;

      postDataApi(requestUrl, infoViewActionsContext, payload, true)
        .then((response: any) => {
          infoViewActionsContext.showMessage(response.message);
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    }
  };

  const handleSave = () => {
    saveData({
      content: localSummary,
    });
    setIsEditing(false);
  };

  return (
    <Fragment>
      <Form
        initialValues={{
          summary: localSummary,
        }}
        onFinish={handleSave}
      >
        <Item name="summary">
          <StyledContent>
            <AppMarkdownEditor
              value={localSummary}
              onChange={setLocalSummary}
              rows={8}
              bordered={false}
            />
          </StyledContent>
        </Item>
        <Flex justify="flex-end" gap="10px">
          <StyledSecoundryButton
            onClick={() => setIsEditing(false)}
            type="default"
          >
            Cancel
          </StyledSecoundryButton>
          <StyledPrimaryButton type="primary" size="small" htmlType="submit">
            Save
          </StyledPrimaryButton>
        </Flex>
      </Form>
    </Fragment>
  );
};

export default SummaryEditar;
