import { useState } from 'react';
import { AppGridContainer, AppTextArea } from '@unpod/components/antd';
import type { RadioChangeEvent } from 'antd';
import { Button, Col, Form, Radio, Row, Space } from 'antd';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { useIntl } from 'react-intl';
import type { Thread } from '@unpod/constants/types';
import type { ApiResponse } from '@/types/common';

type ReportPostProps = {
  post: Thread;
  onReportPost: (post: Thread) => void;
  onClose: () => void;
};

const ReportPost = ({ post, onReportPost, onClose }: ReportPostProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();

  const [value, setValue] = useState('spam');

  const onChange = (e: RadioChangeEvent) => {
    setValue(e.target.value);
  };

  const onSubmitSuccess = (formData: Record<string, unknown>) => {
    postDataApi(`threads/${post?.slug}/report/`, infoViewActionsContext, {
      category: value,
      ...formData,
    })
      .then((response) => {
        const res = response as ApiResponse;
        if (res.message) infoViewActionsContext.showMessage(res.message);
        onReportPost(post);
        onClose();
      })
      .catch((response) => {
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
                    <Radio value="spam">
                      {formatMessage({ id: 'report.spam' })}
                    </Radio>
                    <Radio value="irrelevant">
                      {formatMessage({ id: 'report.irrelevant' })}
                    </Radio>
                    <Radio value="nudity">
                      {formatMessage({ id: 'report.nudity' })}
                    </Radio>
                    <Radio value="controversial">
                      {formatMessage({ id: 'report.controversial' })}
                    </Radio>
                    <Radio value="other">
                      {formatMessage({ id: 'report.other' })}
                    </Radio>
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
                      message: formatMessage({
                        id: 'validation.enterDescription',
                      }),
                    },
                  ]}
                >
                  <AppTextArea
                    placeholder={formatMessage({ id: 'form.description' })}
                  />
                </Form.Item>
              </Col>
            ) : null}
            <Col sm={24}>
              <Form.Item
                name="message"
                rules={[
                  {
                    required: false,
                    message: formatMessage({ id: 'validation.enterMessage' }),
                  },
                ]}
              >
                <AppTextArea
                  placeholder={formatMessage({ id: 'form.message' })}
                />
              </Form.Item>
            </Col>
          </AppGridContainer>

          <Row>
            <Button type="primary" htmlType="submit">
              {formatMessage({ id: 'report.reportPost' })}
            </Button>
          </Row>
        </Form>
      </Col>
    </AppGridContainer>
  );
};

export default ReportPost;
