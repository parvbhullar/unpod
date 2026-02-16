import type { VoiceProfile } from '@unpod/constants/types';

import { useEffect, useRef, useState } from 'react';
import { Space, Tooltip, Typography } from 'antd';
import { MdOutlinePause, MdOutlinePlayArrow } from 'react-icons/md';
import { useTheme } from 'styled-components';
import { clsx } from 'clsx';
import { useMediaQuery } from 'react-responsive';
import { IoMdClose } from 'react-icons/io';

import { MobileWidthQuery } from '@unpod/constants';
import { LANGUAGE_NAMES } from '@unpod/constants/CommonConsts';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';

import {
  PlayButton,
  StyledButton,
  StyledCard,
  StyledCostLabel,
  StyledLanguageTag,
  StyledMetric,
  StyledMetricBar,
  StyledMetricBarContainer,
  StyledMetricsRow,
  StyledProfileContent,
  StyledProfileMain,
  StyledProviderTag,
  StyledText,
  StyledValueTag,
} from './index.styled';

const { Text } = Typography;

type PlayPauseButtonProps = {
  data: VoiceProfile;
  isSelected?: boolean;
  theme?: any;
};

const PlayPauseButton = ({ data, isSelected, theme }: PlayPauseButtonProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();

  const [loading, setLoading] = useState(false);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [isPlaying, setPlaying] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    audioRef.current = null;
    setFileUrl(null);
    setPlaying(false);
  }, [data]);

  const onPlaySound = () => {
    if (fileUrl) {
      if (isPlaying) {
        audioRef.current?.pause();
        setPlaying(false);
      } else {
        audioRef.current?.play();
        setPlaying(true);
      }
    } else {
      setLoading(true);
      getDataApi(
        `/core/voices/${data.agent_profile_id}/`,
        infoViewActionsContext,
        {},
        true,
        {},
        'arraybuffer',
      )
        .then((arrayBuffer: any) => {
          const blob = new Blob([arrayBuffer as BlobPart], {
            type: 'audio/mpeg',
          });
          const url = URL.createObjectURL(blob);

          audioRef.current = new Audio(url);
          setFileUrl(url);
          audioRef.current?.play();
          if (audioRef.current) {
            audioRef.current.onended = () => {
              setPlaying(false);
            };
          }
          setLoading(false);
          setPlaying(true);
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
          setLoading(false);
        });
    }
  };

  const primaryColor = theme?.palette?.primary || '#796cff';
  const borderColor = isPlaying || isSelected ? primaryColor : '#d1d5db';

  return (
    <Tooltip title={isPlaying ? 'Pause' : 'Play'}>
      <PlayButton
        shape="circle"
        icon={
          isPlaying ? (
            <MdOutlinePause fontSize={20} />
          ) : (
            <MdOutlinePlayArrow fontSize={20} />
          )
        }
        onClick={(e) => {
          e.stopPropagation();
          onPlaySound();
        }}
        loading={loading}
        borderColor={borderColor}
        primaryColor={primaryColor}
        isPlaying={isPlaying}
        isSelected={isSelected}
      />
    </Tooltip>
  );
};

const getCostColor = (cost?: string) => {
  if (!cost) return { color: '#d1d5db', width: '0%' };
  const value = parseFloat(cost);
  if (value <= 0.06) return { color: '#22c55e', width: '45%' };
  if (value <= 0.08) return { color: '#eab308', width: '65%' };
  return { color: '#ef4444', width: '80%' };
};

const getLatencyColor = (latency?: string) => {
  if (!latency) return { color: '#d1d5db', width: '0%' };
  const value = parseFloat(latency);
  if (value <= 680) return { color: '#22c55e', width: '55%' };
  if (value <= 800) return { color: '#eab308', width: '70%' };
  return { color: '#ef4444', width: '75%' };
};

type VoiceProfileCardProps = {
  data: VoiceProfile;
  onProfileSelect?: (profile: VoiceProfile | null) => void;
  hideSelect?: boolean;
  selected?: boolean;
};

const VoiceProfileCard = ({
  data,
  onProfileSelect,
  hideSelect,
  selected = false,
}: VoiceProfileCardProps) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(MobileWidthQuery);
  const { name, gender, transcriber, voice } = data;

  const provider = voice?.name || transcriber?.name || 'N/A';

  // Get language/accent display
  const languages = data.voice?.languages?.map((item) =>
    item.code.toUpperCase(),
  ) || ['EN'];

  const genderText = gender === 'F' ? 'Female' : 'Male';

  const onProfileClick = () => {
    if (!hideSelect) {
      onProfileSelect?.(data);
    }
  };

  const onCloseClick = () => {
    onProfileSelect?.(null);
  };

  const costMetric = getCostColor(data.estimated_cost);
  const latencyMetric = getLatencyColor(data.latency);

  return (
    <StyledCard
      className={clsx({ selected: selected })}
      onClick={onProfileClick}
    >
      {!isMobile && (
        <PlayPauseButton data={data} isSelected={selected} theme={theme} />
      )}

      <StyledProfileContent>
        <StyledProfileMain>
          {isMobile && (
            <PlayPauseButton data={data} isSelected={selected} theme={theme} />
          )}

          <StyledText className="profile-name" strong>
            {name}
          </StyledText>
          <Space size={4} style={{ flex: 1, flexWrap: 'wrap' }}>
            <Text style={{ fontSize: 13 }} type="secondary">
              {genderText}
            </Text>
            <Text style={{ fontSize: 13, color: '#d1d5db' }}>·</Text>
            {languages.map((lang) => (
              <Tooltip key={lang} title={LANGUAGE_NAMES[lang] || lang}>
                <StyledLanguageTag>{lang}</StyledLanguageTag>
              </Tooltip>
            ))}
          </Space>
          <StyledProviderTag>{provider}</StyledProviderTag>
        </StyledProfileMain>

        <StyledMetricsRow>
          <StyledMetric>
            <StyledCostLabel type="secondary">COST</StyledCostLabel>
            <StyledMetricBarContainer>
              <StyledMetricBar
                style={{
                  background: costMetric.color,
                  width: costMetric.width,
                }}
              />
            </StyledMetricBarContainer>
            <StyledValueTag>{data.estimated_cost || 'N/A'}</StyledValueTag>
          </StyledMetric>

          <StyledMetric>
            <StyledCostLabel type="secondary">LATENCY</StyledCostLabel>
            <StyledMetricBarContainer>
              <StyledMetricBar
                style={{
                  background: latencyMetric.color,
                  width: latencyMetric.width,
                }}
              />
            </StyledMetricBarContainer>
            <StyledValueTag>{data.latency || 'N/A'}</StyledValueTag>
          </StyledMetric>
        </StyledMetricsRow>
      </StyledProfileContent>

      {hideSelect && (
        <StyledButton
          icon={<IoMdClose size={14} />}
          onClick={(e) => {
            e.stopPropagation();
            onCloseClick();
          }}
          danger
        />
      )}
    </StyledCard>
  );
};

export default VoiceProfileCard;
