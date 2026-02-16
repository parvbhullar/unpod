'use client';
import React from 'react';
import { Typography } from 'antd';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { StyledRoot } from './index.styled';
import AppLink from '@unpod/components/next/AppLink';
import { useIntl } from 'react-intl';

const { Paragraph, Title } = Typography;

const TermsConditions = () => {
  const { formatMessage } = useIntl();

  return (
    <AppPageSection
      heading={<Title>{formatMessage({ id: 'terms.title' })}</Title>}
    >
      <StyledRoot>
        <Paragraph>{formatMessage({ id: 'terms.lastUpdated' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.intro' })}</Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'terms.interpretationTitle' })}
        </Title>
        <Title level={3}>
          {formatMessage({ id: 'terms.interpretationSubTitle' })}
        </Title>
        <Paragraph>
          {formatMessage({ id: 'terms.interpretationDesc' })}
        </Paragraph>

        <Title level={3}>
          {formatMessage({ id: 'terms.definitionsSubTitle' })}
        </Title>
        <Paragraph>{formatMessage({ id: 'terms.definitionsIntro' })}</Paragraph>

        <ul>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'terms.defAffiliateLabel' })}
              </strong>{' '}
              {formatMessage({ id: 'terms.defAffiliateDesc' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>{formatMessage({ id: 'terms.defCountryLabel' })}</strong>{' '}
              {formatMessage({ id: 'terms.defCountryDesc' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>{formatMessage({ id: 'terms.defCompanyLabel' })}</strong>{' '}
              {formatMessage({ id: 'terms.defCompanyDesc' })}
            </Paragraph>
            <Paragraph>{formatMessage({ id: 'terms.defCIN' })}</Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>{formatMessage({ id: 'terms.defDeviceLabel' })}</strong>{' '}
              {formatMessage({ id: 'terms.defDeviceDesc' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>{formatMessage({ id: 'terms.defServiceLabel' })}</strong>{' '}
              {formatMessage({ id: 'terms.defServiceDesc' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>{formatMessage({ id: 'terms.defTermsLabel' })}</strong>{' '}
              {formatMessage({ id: 'terms.defTermsDesc' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>
                {formatMessage({ id: 'terms.defThirdPartyLabel' })}
              </strong>{' '}
              {formatMessage({ id: 'terms.defThirdPartyDesc' })}
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>{formatMessage({ id: 'terms.defWebsiteLabel' })}</strong>{' '}
              {formatMessage({ id: 'terms.defWebsiteDesc' })}{' '}
              <AppLink href="https://unpod.ai/">https://unpod.ai/</AppLink>
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              <strong>{formatMessage({ id: 'terms.defYouLabel' })}</strong>{' '}
              {formatMessage({ id: 'terms.defYouDesc' })}
            </Paragraph>
          </li>
        </ul>

        <Title level={2}>
          {formatMessage({ id: 'terms.acknowledgmentTitle' })}
        </Title>
        <Paragraph>{formatMessage({ id: 'terms.ackPara1' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.ackPara2' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.ackPara3' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.ackPara4' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.ackPara5' })}</Paragraph>

        <Title level={2}>{formatMessage({ id: 'terms.linksTitle' })}</Title>
        <Paragraph>{formatMessage({ id: 'terms.linksPara1' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.linksPara2' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.linksPara3' })}</Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'terms.terminationTitle' })}
        </Title>
        <Paragraph>{formatMessage({ id: 'terms.terminationPara1' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.terminationPara2' })}</Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'terms.limitationTitle' })}
        </Title>
        <Paragraph>{formatMessage({ id: 'terms.limitationPara' })}</Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'terms.disclaimerTitle' })}
        </Title>
        <Paragraph>{formatMessage({ id: 'terms.disclaimerPara1' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.disclaimerPara2' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.disclaimerPara3' })}</Paragraph>

        <Title level={2}>{formatMessage({ id: 'terms.governingTitle' })}</Title>
        <Paragraph>{formatMessage({ id: 'terms.governingPara' })}</Paragraph>

        <Title level={2}>{formatMessage({ id: 'terms.disputesTitle' })}</Title>
        <Paragraph>{formatMessage({ id: 'terms.disputesPara' })}</Paragraph>

        <Title level={2}>{formatMessage({ id: 'terms.euTitle' })}</Title>
        <Paragraph>{formatMessage({ id: 'terms.euPara' })}</Paragraph>

        <Title level={2}>{formatMessage({ id: 'terms.usTitle' })}</Title>
        <Paragraph>{formatMessage({ id: 'terms.usPara' })}</Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'terms.severabilityTitle' })}
        </Title>
        <Title level={3}>
          {formatMessage({ id: 'terms.severabilitySubTitle' })}
        </Title>
        <Paragraph>{formatMessage({ id: 'terms.severabilityPara' })}</Paragraph>

        <Title level={3}>{formatMessage({ id: 'terms.waiverSubTitle' })}</Title>
        <Paragraph>{formatMessage({ id: 'terms.waiverPara' })}</Paragraph>

        <Title level={2}>
          {formatMessage({ id: 'terms.translationTitle' })}
        </Title>
        <Paragraph>{formatMessage({ id: 'terms.translationPara' })}</Paragraph>

        <Title level={2}>{formatMessage({ id: 'terms.changesTitle' })}</Title>
        <Paragraph>{formatMessage({ id: 'terms.changesPara1' })}</Paragraph>
        <Paragraph>{formatMessage({ id: 'terms.changesPara2' })}</Paragraph>

        <Title level={2}>{formatMessage({ id: 'terms.contactTitle' })}</Title>
        <Paragraph>{formatMessage({ id: 'terms.contactIntro' })}</Paragraph>
        <ul>
          <li>
            <Paragraph>
              {formatMessage({ id: 'terms.contactEmailLabel' })}{' '}
              <AppLink href="mailto:info@unpod.ai">info@unpod.ai</AppLink>
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              {formatMessage({ id: 'terms.contactWebLabel' })}{' '}
              <AppLink href="https://unpod.ai/">https://unpod.ai/</AppLink>
            </Paragraph>
          </li>
        </ul>
      </StyledRoot>
    </AppPageSection>
  );
};

export default TermsConditions;
