import {useState} from 'react';
import {AppGridContainer, AppTextArea} from '@unpod/components/antd';
import {Button, Col, Form, Radio, type RadioChangeEvent, Row, Space,} from 'antd';
import {postDataApi, useInfoViewActionsContext} from '@unpod/providers';

type ReportPostProps = {
  post: any;
  onReportPost: (post: any) => void;
  onClose: () => void;
};

const ReportPost = ({post, onReportPost, onClose}: ReportPostProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();

  const [value, setValue] = useState('spam');

  const onChange = (e: RadioChangeEvent) => {
    setValue(e.target.value);
  };

  const onSubmitSuccess = (formData: Record<string, any>) => {
    postDataApi(`threads/${post?.slug}/report/`, infoViewActionsContext, {
      category: value,
      ...formData,
    })
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        onReportPost(post);
        onClose();
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  return (
    <AppGridContainer>
      <Col sm={24} md={24}>
        <Form onFinish={onSubmitSuccess}>
          <AppGridContainer>
            <Col sm={24}>
              <Form.Item>
                <Radio.Group onChange={onChange} value={value}>
                  <Space orientation="vertical">
                    <Radio value="spam">Spam</Radio>
                    <Radio value="irrelevant">Irrelevant</Radio>
                    <Radio value="nudity">Nudity</Radio>
                    <Radio value="controversial">Controversial</Radio>
                    <Radio value="other">Other</Radio>
                  </Space>
                </Radio.Group>
              </Form.Item>
            </Col>
            {value === 'other' ? (
              <Col sm={24}>
                <Form.Item
                  name="other"
                  rules={[
                    {
                      required: true,
                      message: `Please enter description!`,
                    },
                  ]}
                >
                  <AppTextArea placeholder="Description"/>
                </Form.Item>
              </Col>
            ) : null}
            <Col sm={24}>
              <Form.Item
                name="message"
                rules={[
                  {
                    required: false,
                    message: `Please enter message!`,
                  },
                ]}
              >
                <AppTextArea placeholder="Message"/>
              </Form.Item>
            </Col>
          </AppGridContainer>

          <Row>
            <Button type="primary" htmlType="submit">
              Report Post
            </Button>
          </Row>
        </Form>
      </Col>
    </AppGridContainer>
  );
};

export default ReportPost;
