import { useEffect, useState } from 'react';
import { StyledFlex, StyledGridContainer } from './index.styled';
import BillingInfoRow from './BillingInfoRow';
import { FaRegEdit } from 'react-icons/fa';
import { Button, Typography } from 'antd';
import EditBillingInfo from '../EditBilling';
import { useAuthContext } from '@unpod/providers';
import { isEmptyObject } from '@unpod/helpers/GlobalHelper';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';
import { useIntl } from 'react-intl';

const { Title } = Typography;

const ViewBillingInfo = () => {
  const [isEditing, setIsEditing] = useState(false);
  const { activeOrg } = useAuthContext();
  const mobileScreen = useMediaQuery(MobileWidthQuery);
  const { formatMessage } = useIntl();

  const billingInfo = (activeOrg as any)?.billing_info || {};

  useEffect(() => {
    if (!isEmptyObject(billingInfo as any) && activeOrg) {
      if (!billingInfo.contact_person) setIsEditing(true);
    }
  }, [billingInfo, activeOrg]);

  const {
    contact_person,
    email,
    phone_number,
    phone_number_cc,
    address_line1,
    address_line2,
    city,
    state,
    country,
    postal_code,
    tax_ids = [],
  } = billingInfo || {};

  if (isEditing) {
    return (
      <EditBillingInfo setIsEditing={setIsEditing} billingInfo={billingInfo} />
    );
  }
  return (
    <StyledGridContainer>
      <Title style={{ marginBottom: 12 }} level={mobileScreen ? 5 : 3}>
        {formatMessage({ id: 'billingInfo.title' })}
      </Title>

      <BillingInfoRow
        label={formatMessage({ id: 'billingInfo.contactPerson' })}
        value={contact_person || '-'}
      />

      <BillingInfoRow
        label={formatMessage({ id: 'billingInfo.email' })}
        value={email}
      />

      <BillingInfoRow
        label={formatMessage({ id: 'billingInfo.phoneNumber' })}
        value={phone_number ? `${phone_number_cc} ${phone_number}` : '-'}
      />

      <BillingInfoRow
        label={formatMessage({ id: 'billingInfo.billingAddress' })}
        value={[
          address_line1,
          address_line2,
          city && postal_code ? `${city}, ${postal_code}` : city || postal_code,
          state,
          country,
        ]
          .filter(Boolean)
          .join('<br />')}
      />

      {tax_ids?.map((tax: any, index: number) => (
        <BillingInfoRow
          key={`tax-id-${index}`}
          label={formatMessage({ id: 'billingInfo.taxId' })}
          value={
            tax ? `${tax.country || country} (${tax.type}) ${tax.number}` : '-'
          }
        />
      ))}

      <StyledFlex justify="flex-start">
        <Button
          type="primary"
          ghost
          icon={<FaRegEdit size={16} />}
          onClick={() => setIsEditing(true)}
        >
          {formatMessage({ id: 'common.update' })}
        </Button>
      </StyledFlex>
    </StyledGridContainer>
  );
};

export default ViewBillingInfo;
