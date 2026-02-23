import {useEffect} from 'react';
import {Button, Form} from 'antd';
import {AppInput, AppTextArea, DrawerForm, DrawerFormFooter,} from '@unpod/components/antd';
import {postDataApi, putDataApi, useInfoViewActionsContext,} from '@unpod/providers';
import {DrawerBody} from '@unpod/components/antd/AppDrawer/DrawerBody';
import {useIntl} from 'react-intl';

const {Item, useForm} = Form;

const AddTagForm = ({
                      selectedTag,
                      currentSpace,
                      onTagSaved,
                    }: {
  selectedTag?: any;
  currentSpace: any;
  onTagSaved: (data: any) => void;
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [form] = useForm();
  const {formatMessage} = useIntl();

  useEffect(() => {
    if (selectedTag) {
      form.setFieldsValue(selectedTag);
    }
  }, [selectedTag]);

  const onSubmitSuccess = (formData: any) => {
    const payload = {
      ...formData,
      type: 'email',
      content_type_model: 'space',
      slug: currentSpace.slug,
    };

    if (selectedTag) {
      payload['old-slug'] = selectedTag.slug;
      putDataApi(`core/relevant-tags/update/`, infoViewActionsContext, payload)
        .then((response: any) => {
          infoViewActionsContext.showMessage(response.message);
          form.resetFields();
          onTagSaved(response.data);
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    } else {
      postDataApi(`core/relevant-tags/create/`, infoViewActionsContext, payload)
        .then((response: any) => {
          infoViewActionsContext.showMessage(response.message);
          form.resetFields();
          onTagSaved(response.data);
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    }
  };

  return (
    <DrawerForm form={form} onFinish={onSubmitSuccess}>
      <DrawerBody>
        <Item
          name="name"
          rules={[
            {
              required: true,
              message: formatMessage({id: 'manageLabels.nameError'}),
            },
          ]}
        >
          <AppInput placeholder={formatMessage({id: 'form.name'})}/>
        </Item>

        <Item name="description">
          <AppTextArea
            placeholder={formatMessage({id: 'form.description'})}
          />
        </Item>
      </DrawerBody>
      <DrawerFormFooter>
        <Button type="primary" htmlType="submit">
          {formatMessage({id: 'manageLabels.save'})}
        </Button>
      </DrawerFormFooter>
    </DrawerForm>
  );
};

export default AddTagForm;
