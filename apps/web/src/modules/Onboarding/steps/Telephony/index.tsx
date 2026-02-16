import React, { Fragment, useEffect, useState } from 'react';
import { Badge, Button, Flex, Select, Typography } from 'antd';
import { useIntl } from 'react-intl';
import { useGetDataApi } from '@unpod/providers';
import { MdRefresh } from 'react-icons/md';
import { StyledContainer, StyledNumber } from './index.styled';
import { FooterBar } from '@/modules/Onboarding/index.styled';
import { regionOptions } from '@unpod/constants/CountryData';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery, TabWidthQuery } from '@unpod/constants';
import type { Pilot } from '@unpod/constants/types';

const { Text } = Typography;

type TelephonyNumber = {
  number?: string;
};


type TelephonyProps = {
  agent: Pilot;
  updateAgentData: (
    formData: FormData,
    setLoading: React.Dispatch<React.SetStateAction<boolean>>,
    nextStep?: string,
  ) => void;
};

const Telephony: React.FC<TelephonyProps> = ({ agent, updateAgentData }) => {
  const { formatMessage } = useIntl();
  const [number, setNumber] = useState<TelephonyNumber | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState('IN');
  const [isOpenSelect, setIsOpenSelect] = useState(false);
  const [tempRegion, setTempRegion] = useState(selectedRegion);
  const mobileScreen = useMediaQuery(MobileWidthQuery);
  const tabletScreen = useMediaQuery(TabWidthQuery);

  const [{ loading, apiData: numbers }, { setQueryParams }] =
    useGetDataApi<TelephonyNumber[]>(
      `core/telephony-numbers/`,
      { data: [] },
      { type: 'agent', region: selectedRegion },
      true,
      (res) => {
        if (res?.data?.length) {
          const index = Math.floor(Math.random() * res.data.length);
          setNumber(res.data[index]);
        }
      },
    );

  const onSubmit = (isManual = false) => {
    const formData = new FormData();

    const updatedTelephonyConfig = {
      ...(agent.telephonyConfig || {}),
      telephony: [number],
    };

    formData.append('name', agent.name || '');
    formData.append('handle', agent.handle || '');
    formData.append('telephony_config', JSON.stringify(updatedTelephonyConfig));
    formData.append('region', selectedRegion);

    if (isManual) {
      updateAgentData(formData, setIsLoading, '5');
    } else {
      updateAgentData(formData, setIsLoading);
    }
  };

  useEffect(() => {
    setQueryParams({ type: 'agent', region: selectedRegion });
    if (number) {
      onSubmit(false);
    }
  }, [selectedRegion]);

  const getNumber = () => {
    if (!numbers?.data?.length) return;
    const index = Math.floor(Math.random() * numbers.data.length);
    return setNumber(numbers.data[index]);
  };

  return (
    <Fragment>
      <StyledContainer>
        <Text type="secondary">
          {formatMessage({ id: 'identityOnboarding.aiWillAnswer' })}
        </Text>
        <Flex align="center" gap={mobileScreen ? 12 : 32}>
          <StyledNumber>
            {number ? number.number : '+91 000 000 0000'}
          </StyledNumber>

          <Button
            type="primary"
            shape="circle"
            size={tabletScreen ? 'middle' : 'large'}
            icon={!loading && <MdRefresh fontSize={22} />}
            loading={loading}
            onClick={getNumber}
            ghost
          />
        </Flex>
        <Flex align="center" gap={5}>
          {!isOpenSelect ? (
            <Text>
              {regionOptions.find((r) => r.value === selectedRegion)?.label ||
                formatMessage({ id: 'identityOnboarding.selectRegion' })}
            </Text>
          ) : (
            <Select
              placeholder={formatMessage({
                id: 'identityOnboarding.selectRegion',
              })}
              options={regionOptions}
              value={tempRegion}
              onChange={(value) => setTempRegion(String(value))}
              style={{ minWidth: mobileScreen ? 100 : 180 }}
            />
          )}
          <Badge dot={true} status="default" />

          {!isOpenSelect ? (
            <Button type="link" onClick={() => setIsOpenSelect(true)}>
              {formatMessage({ id: 'identityOnboarding.changeRegion' })}
            </Button>
          ) : (
            <Flex gap={mobileScreen ? 0 : 10} align="center">
              <Button
                type="link"
                onClick={() => {
                  setSelectedRegion(tempRegion);
                  setIsOpenSelect(false);
                }}
              >
                {formatMessage({ id: 'common.ok' })}
              </Button>

              <Button type="link" onClick={() => setIsOpenSelect(false)}>
                {formatMessage({ id: 'common.cancel' })}
              </Button>
            </Flex>
          )}
        </Flex>
      </StyledContainer>

      <FooterBar>
        <Flex justify="flex-end">
          <Button
            type="primary"
            disabled={!number}
            onClick={() => onSubmit(true)}
            style={{ paddingInline: 24 }}
            loading={isLoading}
          >
            {formatMessage({ id: 'identityOnboarding.continue' })}
          </Button>
        </Flex>
      </FooterBar>
    </Fragment>
  );
};

export default Telephony;
