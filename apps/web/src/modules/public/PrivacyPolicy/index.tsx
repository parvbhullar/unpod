'use client';
import React from 'react';
import { Typography } from 'antd';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { StyledRoot } from './index.styled';
import AppLink from '@unpod/components/next/AppLink';
import { useIntl } from 'react-intl';

const { Paragraph, Title } = Typography;

const PrivacyPolicy = () => {
  const { formatMessage } = useIntl();
  return (
    <AppPageSection
      heading={<Title>{formatMessage({ id: 'privacyPolicy.title' })}</Title>}
    >
      <StyledRoot>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.lastUpdated' })}
        </Paragraph>
        <Paragraph>{formatMessage({ id: 'privacyPolicy.intro1' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'privacyPolicy.intro2' })}</Paragraph>
        <Title level={2}>
          {formatMessage({ id: 'privacyPolicy.interpretation' })}
        </Title>
        <Title level={3}>
          {formatMessage({ id: 'privacyPolicy.interpretationTitle' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.interpretationDescription' })}
        </Paragraph>
        <Title level={3}>
          {formatMessage({ id: 'privacyPolicy.definitions' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.forPurpose' })}
        </Paragraph>
        <ul>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.accountTitle' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.account' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.affiliateTitle' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.affiliate' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.companyTitle' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.company' })}
            </Paragraph>
            <Paragraph>CIN - U62010PB2025PTC066615</Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.cookiesName' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.cookies' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.countryTitle' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.country' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.deviceTitle' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.device' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.personalDataTitle' })}:{' '}
              </strong>
              {formatMessage({ id: 'privacyPolicy.personalDataDesc' })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.serviceTitle' })}:{' '}
              </strong>
              {formatMessage({ id: 'privacyPolicy.serviceDesc' })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.serviceProviderTitle' })}
                :{' '}
              </strong>
              {formatMessage({ id: 'privacyPolicy.serviceProviderDesc' })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.thirdPartySocialTitle' })}
                :{' '}
              </strong>
              {formatMessage({ id: 'privacyPolicy.thirdPartySocialDesc' })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.usageDataTitle' })}:
              </strong>
              {formatMessage({ id: 'privacyPolicy.usageDataDesc' })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.websiteTitle' })}:{' '}
              </strong>
              {formatMessage({ id: 'privacyPolicy.websiteDesc' })}{' '}
              <AppLink href="https://unpod.ai/">https://unpod.ai/</AppLink>
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.youTitle' })}:{' '}
              </strong>
              {formatMessage({ id: 'privacyPolicy.youDesc' })}
            </Paragraph>
          </li>
        </ul>
        <Title level={2}>
          {formatMessage({ id: 'privacyPolicy.collectingTitle' })}
        </Title>
        <Title level={3}>
          {formatMessage({ id: 'privacyPolicy.typesOfData' })}
        </Title>
        <Title level={4}>
          {formatMessage({ id: 'privacyPolicy.personalDataTitle' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.personalDataCollected' })}
        </Paragraph>
        <ul>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.data.email' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.data.name' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.data.phone' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.data.jobRole' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.data.company' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.data.address' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.data.usage' })}
            </Paragraph>
          </li>
        </ul>
        <Title level={4}>
          {formatMessage({ id: 'privacyPolicy.usageData' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.usageDataPara1' })}
        </Paragraph>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.usageDataPara2' })}
        </Paragraph>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.usageDataPara3' })}
        </Paragraph>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.usageDataPara4' })}
        </Paragraph>
        <Title level={4}>
          {formatMessage({ id: 'privacyPolicy.thirdPartyInfoTitle' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.thirdPartyInfoDesc' })}
        </Paragraph>
        <ul>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.google' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.facebook' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.instagram' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.twitter' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.linkedIn' })}
            </Paragraph>
          </li>
        </ul>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.thirdPartySocialAccessDesc' })}
        </Paragraph>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.thirdPartySocialAdditional' })}
        </Paragraph>

        <Title level={4}>
          {formatMessage({ id: 'privacyPolicy.technologiesAndCookies' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.technologiesAndCookiesDes' })}
        </Paragraph>
        <ul>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({
                  id: 'privacyPolicy.cookiesTitle',
                })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.cookiesText' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.webBeaconsTitle' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.webBeaconsText' })}
            </Paragraph>
          </li>
        </ul>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.cookieTypesText' })}
        </Paragraph>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.cookieUsageText' })}
        </Paragraph>
        <ul>
          <li>
            <Paragraph strong>
              {formatMessage({ id: 'privacyPolicy.necessaryCookiesTitle' })}
            </Paragraph>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.necessaryCookiesType' })}
            </Paragraph>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.necessaryCookiesAdmin' })}
            </Paragraph>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.necessaryCookiesPurpose' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph strong>
              {formatMessage({ id: 'privacyPolicy.acceptanceCookiesTitle' })}
            </Paragraph>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.acceptanceCookiesType' })}
            </Paragraph>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.acceptanceCookiesAdmin' })}
            </Paragraph>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.acceptanceCookiesPurpose' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph strong>
              {formatMessage({ id: 'privacyPolicy.functionalityCookiesTitle' })}
            </Paragraph>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.functionalityCookiesType' })}
            </Paragraph>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.functionalityCookiesAdmin' })}
            </Paragraph>
            <Paragraph>
              {formatMessage({
                id: 'privacyPolicy.functionalityCookiesPurpose',
              })}
            </Paragraph>
          </li>
        </ul>

        <Paragraph>
          {formatMessage({
            id: 'privacyPolicy.moreInfoText',
          })}
        </Paragraph>
        <Title level={3}>
          {formatMessage({
            id: 'privacyPolicy.personalDataUse',
          })}
        </Title>
        <Paragraph>
          {formatMessage({
            id: 'privacyPolicy.personalDataIntro',
          })}
        </Paragraph>
        <ul>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({
                  id: 'privacyPolicy.purpose.serviceTitle',
                })}
              </strong>{' '}
              {formatMessage({
                id: 'privacyPolicy.purpose.serviceText',
              })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({
                  id: 'privacyPolicy.purpose.accountTitle',
                })}
                :
              </strong>{' '}
              {formatMessage({
                id: 'privacyPolicy.purpose.accountText',
              })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({
                  id: 'privacyPolicy.purpose.contractTitle',
                })}
                :{' '}
              </strong>
              {formatMessage({
                id: 'privacyPolicy.purpose.contractText',
              })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {' '}
                {formatMessage({
                  id: 'privacyPolicy.purpose.contactTitle',
                })}
                :{' '}
              </strong>
              {formatMessage({
                id: 'privacyPolicy.purpose.contactText',
              })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {' '}
                {formatMessage({
                  id: 'privacyPolicy.purpose.offersTitle',
                })}{' '}
              </strong>
              {formatMessage({
                id: 'privacyPolicy.purpose.offersText',
              })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {' '}
                {formatMessage({
                  id: 'privacyPolicy.purpose.requestsTitle',
                })}
                :{' '}
              </strong>
              {formatMessage({
                id: 'privacyPolicy.purpose.requestsText',
              })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({
                  id: 'privacyPolicy.purpose.businessTransfersTitle',
                })}
                :{' '}
              </strong>
              {formatMessage({
                id: 'privacyPolicy.purpose.businessTransfersText',
              })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {' '}
                {formatMessage({
                  id: 'privacyPolicy.purpose.otherTitle',
                })}
                :{' '}
              </strong>
              {formatMessage({
                id: 'privacyPolicy.purpose.otherText',
              })}
            </Paragraph>
          </li>
        </ul>
        <Paragraph>
          {formatMessage({
            id: 'privacyPolicy.dataSharingIntro',
          })}
          :
        </Paragraph>
        <ul>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({
                  id: 'privacyPolicy.withServiceProvidersTitle',
                })}
              </strong>{' '}
              {formatMessage({
                id: 'privacyPolicy.withServiceProvidersDesc',
              })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({
                  id: 'privacyPolicy.businessTransfersTitle',
                })}
              </strong>{' '}
              {formatMessage({
                id: 'privacyPolicy.businessTransfersDesc',
              })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.affiliatesTitle' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.affiliatesDesc' })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({
                  id: 'privacyPolicy.businessPartnersTitle',
                })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.businessPartnersDesc' })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.otherUsersTitle' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.otherUsersDesc' })}
            </Paragraph>
          </li>

          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'privacyPolicy.consentTitle' })}
              </strong>{' '}
              {formatMessage({ id: 'privacyPolicy.consentDesc' })}
            </Paragraph>
          </li>
        </ul>

        <Title level={3}>
          {formatMessage({ id: 'privacyPolicy.retentionTitle' })}
        </Title>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.retentionDesc1' })}
        </Paragraph>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.retentionDesc2' })}
        </Paragraph>

        <Title level={3}>
          {formatMessage({ id: 'privacyPolicy.transferTitle' })}
        </Title>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.transferDesc1' })}
        </Paragraph>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.transferDesc2' })}
        </Paragraph>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.transferDesc3' })}
        </Paragraph>

        <Title level={3}>
          {formatMessage({ id: 'privacyPolicy.deleteTitle' })}
        </Title>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.deleteDesc1' })}
        </Paragraph>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.deleteDesc2' })}
        </Paragraph>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.deleteDesc3' })}
        </Paragraph>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.deleteDesc4' })}
        </Paragraph>

        <Title level={3}>
          {formatMessage({ id: 'privacyPolicy.disclosureTitle' })}
        </Title>

        <Title level={4}>
          {formatMessage({ id: 'privacyPolicy.businessTransactionTitle' })}
        </Title>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.businessTransactionDesc' })}
        </Paragraph>

        <Title level={4}>
          {formatMessage({ id: 'privacyPolicy.lawEnforcementTitle' })}
        </Title>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.lawEnforcementDesc' })}
        </Paragraph>

        <Title level={4}>
          {formatMessage({ id: 'privacyPolicy.otherLegalTitle' })}
        </Title>

        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.otherLegalDesc' })}
        </Paragraph>
        <ul>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.legalObligation' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.protectRights' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.preventWrongdoing' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.personalSafety' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.legalLiability' })}
            </Paragraph>
          </li>
        </ul>

        <Title level={3}>
          {formatMessage({ id: 'privacyPolicy.securityTitle' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.securityDesc' })}
        </Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'privacyPolicy.childrenPrivacyTitle' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.childrenPrivacyDesc1' })}
        </Paragraph>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.childrenPrivacyDesc2' })}
        </Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'privacyPolicy.linksTitle' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.linksDesc1' })}
        </Paragraph>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.linksDesc2' })}
        </Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'privacyPolicy.changesTitle' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.changesDesc1' })}
        </Paragraph>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.changesDesc2' })}
        </Paragraph>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.changesDesc3' })}
        </Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'privacyPolicy.contactTitle' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'privacyPolicy.contactDesc' })}
        </Paragraph>

        <ul>
          <li>
            <Paragraph>
              {formatMessage({ id: 'privacyPolicy.contactEmailLabel' })}{' '}
              <AppLink href="mailto:info@unpod.ai">info@unpod.ai</AppLink>
            </Paragraph>
          </li>
        </ul>
      </StyledRoot>
    </AppPageSection>
  );
};

export default PrivacyPolicy;
