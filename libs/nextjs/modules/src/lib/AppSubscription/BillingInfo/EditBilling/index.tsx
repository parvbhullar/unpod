import { Button, Col, Form, Row, Select, Typography } from 'antd';
import AppInput from '@unpod/components/antd/AppInput';
import { AppSelect } from '@unpod/components/antd';
import AppPhoneInput from '@unpod/components/antd/AppPhoneInput';
import AppInputNumber from '@unpod/components/antd/AppInputNumber';
import { taxIdData } from '@unpod/constants/TaxIdList';
import { countryCodes } from '@unpod/constants/CountryData';
import {
  putDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
  useInfoViewContext,
} from '@unpod/providers';
import { SaveOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import {
  StyledButtonWrapper,
  StyledContainer,
  StyledFlex,
  StyledItemRow,
} from './index.styled';
import { MdAdd, MdDelete } from 'react-icons/md';
import { EditBillingInfoSkeleton } from '@unpod/skeleton/EditBillingInfo';
import { useIntl } from 'react-intl';

const { Option } = Select;
const { Item, List } = Form;

const EditBillingInfo = ({
  setIsEditing,
  billingInfo,
}: {
  setIsEditing: (value: boolean) => void;
  billingInfo: any;
}) => {
  const [form] = Form.useForm();
  const infoViewActionsContext = useInfoViewActionsContext();
  const infoViewContext = useInfoViewContext();
  const { setActiveOrg } = useAuthActionsContext();
  const { activeOrg } = useAuthContext();
  const router = useRouter();
  const { formatMessage } = useIntl();

  const handleFinish = (values: any) => {
    putDataApi(
      `organization/${activeOrg?.domain_handle}/billing-info/`,
      infoViewActionsContext,
      {
        ...values,
        phone_number: values.phone_number?.number,
        phone_number_cc: values.phone_number?.countryCode,
      },
    )
      .then((data: any) => {
        infoViewActionsContext.showMessage(
          data.message || formatMessage({ id: 'common.savedSuccess' }),
        );
        setIsEditing(false);
        setActiveOrg({ ...activeOrg, billing_info: data.data });
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(
          error.message || formatMessage({ id: 'common.saveFailed' }),
        );
      });
  };

  const onFinishFailed = (errorInfo: any) => {
    if (errorInfo?.errorFields?.length > 0) {
      infoViewActionsContext.showError(errorInfo.errorFields[0].errors[0]);
    } else {
      infoViewActionsContext.showError(
        formatMessage({ id: 'common.fillRequired' }),
      );
    }
  };

  if (!billingInfo) {
    return <EditBillingInfoSkeleton />;
  }

  return (
    <StyledContainer>
      <Typography.Title style={{ marginBottom: 20 }} level={3}>
        {formatMessage({ id: 'billingInfo.updatedTitle' })}
      </Typography.Title>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleFinish}
        onFinishFailed={onFinishFailed}
        initialValues={{
          ...billingInfo,
          phone_number: {
            number: billingInfo?.phone_number || '',
            countryCode: billingInfo?.phone_number_cc || '+91',
          },
          tax_ids:
            billingInfo?.tax_ids?.length > 0
              ? billingInfo.tax_ids.map((tax: any) => ({
                  type: tax.type,
                  number: tax.number,
                }))
              : [{}],
        }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Item
              name="contact_person"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.contactPerson' }),
                },
              ]}
            >
              <AppInput placeholder={formatMessage({ id: 'form.name' })} />
            </Item>
          </Col>
          <Col xs={24} md={12}>
            <Item
              name="email"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.email' }),
                },
              ]}
            >
              <AppInput placeholder={formatMessage({ id: 'form.email' })} />
            </Item>
          </Col>

          <Col xs={24} md={12}>
            <Item
              name="country"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.email' }),
                },
              ]}
            >
              <AppSelect
                placeholder={formatMessage({ id: 'billingInfo.country' })}
                showSearch
                onChange={(value) => {
                  const selectedCountry = countryCodes.find(
                    (c) => c.name === value,
                  );
                  form.setFieldsValue({
                    phone_number: {
                      countryCode: selectedCountry?.code || '+91',
                      number: '',
                    },

                    tax_ids: [
                      {
                        country: selectedCountry?.code || 'IN',
                        type: '',
                        number: '',
                      },
                    ],
                  });
                }}
              >
                {countryCodes.map((option: any) => (
                  <Option key={option.name} value={option.name}>
                    {`${option.flag} ${option.name}`}
                  </Option>
                ))}
              </AppSelect>
            </Item>
          </Col>

          <Col xs={24} md={12}>
            <Item
              name="address_line1"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.address1' }),
                },
              ]}
            >
              <AppInput
                placeholder={formatMessage({ id: 'billingInfo.address1' })}
              />
            </Item>
          </Col>

          <Col xs={24} md={12}>
            <Item name="address_line2">
              <AppInput
                placeholder={formatMessage({ id: 'billingInfo.address2' })}
              />
            </Item>
          </Col>
          <Col xs={24} md={12}>
            <Item
              name="city"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.city' }),
                },
              ]}
            >
              <AppInput
                placeholder={formatMessage({ id: 'billingInfo.city' })}
              />
            </Item>
          </Col>

          <Col xs={24} md={12}>
            <Item
              name="postal_code"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.postalCode' }),
                },
              ]}
            >
              <AppInputNumber
                placeholder={formatMessage({ id: 'billingInfo.postalCode' })}
              />
            </Item>
          </Col>
          <Col xs={24} md={12}>
            <Item
              name="state"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.state' }),
                },
              ]}
            >
              <AppInput
                placeholder={formatMessage({ id: 'billingInfo.state' })}
              />
            </Item>
          </Col>

          <Col xs={24} md={12}>
            <Item
              name="phone_number"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.phone' }),
                },
              ]}
            >
              <AppPhoneInput />
            </Item>
          </Col>
        </Row>
        <List name="tax_ids">
          {(fields, { add, remove }) => {
            const selectedCountry = form.getFieldValue('country');
            const availableTaxIds = taxIdData.filter(
              (t) => t.country === selectedCountry,
            );

            return (
              <>
                {fields.map(({ key, name }) => (
                  <StyledItemRow key={key}>
                    <Item
                      name={[name, 'type']}
                      rules={[
                        {
                          required: true,
                          message: formatMessage({ id: 'validation.taxType' }),
                        },
                      ]}
                    >
                      <AppSelect
                        placeholder={formatMessage({
                          id: 'billingInfo.taxId',
                        })}
                      >
                        {availableTaxIds.map((tax: any) => (
                          <Option key={tax.taxIdName} value={tax.taxIdName}>
                            {tax.flag} {tax.taxIdName}
                          </Option>
                        ))}
                      </AppSelect>
                    </Item>

                    <Item
                      name={[name, 'number']}
                      rules={[
                        {
                          required: true,
                          message: formatMessage({
                            id: 'validation.taxNumber',
                          }),
                        },
                        ({ getFieldValue }) => ({
                          validator(_, value) {
                            const selectedType = getFieldValue([
                              'tax_ids',
                              name,
                              'type',
                            ]);
                            const taxRule = taxIdData.find(
                              (t) =>
                                t.taxIdName === selectedType &&
                                t.country === selectedCountry,
                            );
                            if (!value || !taxRule?.regex)
                              return Promise.resolve();
                            const regex = new RegExp(taxRule.regex);
                            return regex.test(value)
                              ? Promise.resolve()
                              : Promise.reject(
                                  new Error(
                                    formatMessage(
                                      {
                                        id: 'validation.invalidFormat',
                                      },
                                      { count: selectedType },
                                    ),
                                  ),
                                );
                          },
                        }),
                      ]}
                    >
                      <AppInput
                        placeholder={formatMessage({
                          id: 'billingInfo.taxIdNumber',
                        })}
                      />
                    </Item>

                    <Button
                      type="primary"
                      size="middle"
                      onClick={() => remove(name)}
                      icon={<MdDelete fontSize={18} />}
                      danger
                      ghost
                    />
                  </StyledItemRow>
                ))}

                <StyledButtonWrapper>
                  <Button
                    type="primary"
                    ghost
                    onClick={() => add({ type: '', number: '' })}
                    disabled={fields.length >= availableTaxIds.length}
                    icon={<MdAdd size={16} />}
                  >
                    {formatMessage({ id: 'common.addNew' })}
                  </Button>
                  <StyledFlex align="center">
                    <Button
                      onClick={() => {
                        if (billingInfo?.postal_code) {
                          setIsEditing(false);
                        } else {
                          router.back();
                        }
                      }}
                      style={{ marginRight: 8 }}
                    >
                      {formatMessage({ id: 'common.cancel' })}
                    </Button>
                    <Button
                      type="primary"
                      htmlType="submit"
                      icon={<SaveOutlined />}
                      loading={infoViewContext.loading}
                    >
                      {formatMessage({ id: 'common.save' })}
                    </Button>
                  </StyledFlex>
                </StyledButtonWrapper>
              </>
            );
          }}
        </List>
      </Form>
    </StyledContainer>
  );
};

export default EditBillingInfo;
