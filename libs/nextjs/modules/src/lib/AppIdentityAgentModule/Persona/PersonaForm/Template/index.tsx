'use client';
import { Flex, Form, type FormInstance, Typography } from 'antd';
import { type ReactNode } from 'react';
import {
  StyledCheckableTag,
  StyledSubtitle,
  StyledTemplatesTrack,
} from './index.styled';
import { useGetDataApi } from '@unpod/providers';
import {
  FaBell,
  FaBullhorn,
  FaBullseye,
  FaConciergeBell,
  FaPoll,
  FaShoppingCart,
} from 'react-icons/fa';
import AppGrid from '@unpod/components/common/AppGrid';
import { TemplateSkeleton } from '@unpod/skeleton/TemplateSkeleton';

const { Text } = Typography;

type TemplateItem = {
  id?: string | number;
  name?: string;
  slug?: string;
  description?: string;
};

type TemplateProps = {
  form: FormInstance;
  setIsOpen: (open: boolean) => void;
};

const Template = ({ form, setIsOpen }: TemplateProps) => {
  const [{ apiData, loading }] = useGetDataApi(
    'core/pilot-templates/',
    {
      data: [],
    },
    {},
    true,
  );
  const selectedTemplate = form.getFieldValue('template') as
    | TemplateItem
    | undefined;

  const onTemplateChange = (template: TemplateItem) => {
    form.setFieldsValue({ template: template });
    setIsOpen(false);
  };

  const TEMPLATE_ICONS: Record<string, ReactNode> = {
    'recruitment-agent': '👔',
    'onboarding-agent': '🚀',
    'cod-confirmation-agent': '📦',
    'front-desk-agent': <FaConciergeBell size={24} />,
    'lead-generation-agent': <FaBullhorn size={24} />,
    'reminder-agent': <FaBell size={24} />,
    'cart-abandonment-recovery-agent': <FaShoppingCart size={24} />,
    'announcement-agent': <FaBullseye size={24} />,
    'survey-agent': <FaPoll size={24} />,
    'customer-support-agent': '🎧',
  };

  const isChecked = (template: TemplateItem) =>
    selectedTemplate?.id === template.id;

  const templates = ((apiData as any)?.data ?? []) as TemplateItem[];

  return (
    <Form.Item name="template">
      <StyledTemplatesTrack>
        {loading ? (
          <TemplateSkeleton />
        ) : (
          <AppGrid
            style={{
              height: `calc(100vh - 82px)`,
              overflowY: 'auto',
            }}
            data={templates}
            itemPadding={12}
            responsive={{
              xs: 1,
              sm: 1,
              md: 2,
              lg: 2,
            }}
            renderItem={(item: TemplateItem, index: number) => (
              <StyledCheckableTag
                key={item.id ?? item.name ?? index}
                checked={isChecked(item)}
                onChange={() => onTemplateChange(item)}
              >
                <div style={{ fontSize: 18, marginBottom: 12 }}>
                  {item.slug ? (TEMPLATE_ICONS[item.slug] ?? '🎧') : '🎧'}
                </div>
                <Flex vertical justify="center" align="center">
                  <Text strong style={{ margin: 0 }}>
                    {item.name}
                  </Text>
                  <div style={{ width: 250, display: 'block' }}>
                    <StyledSubtitle type="secondary" className={'mb-0'}>
                      {item.description}
                    </StyledSubtitle>
                  </div>
                </Flex>
              </StyledCheckableTag>
            )}
          />
        )}
      </StyledTemplatesTrack>
    </Form.Item>
  );
};

export default Template;
