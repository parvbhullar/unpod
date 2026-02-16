/**
 * Please refer the following docs for more detals.
 * https://www.100ms.live/docs/javascript/v2/how--to-guides/extend-capabilities/plugins/virtual-background
 */
import { useEffect, useRef, useState } from 'react';
import { HMSVirtualBackgroundTypes } from '@100mslive/hms-virtual-background';
import {
  selectIsAllowedToPublish,
  selectIsLocalVideoPluginPresent,
  selectLocalPeerRole,
  selectLocalVideoTrackID,
  useHMSActions,
  useHMSStore,
} from '@100mslive/react-sdk';
import { useIsFeatureEnabled } from '../../hooks/useFeatures';
import { getRandomVirtualBackground } from './vbutils';
import { FEATURE_LIST } from '../../common/constants';
import { Button, Tooltip } from 'antd';
import { RxShadow } from 'react-icons/rx';

export const VirtualBackground = () => {
  const pluginRef = useRef(null);
  const hmsActions = useHMSActions();
  const isAllowedToPublish = useHMSStore(selectIsAllowedToPublish);
  const role = useHMSStore(selectLocalPeerRole);
  const [isVBLoading, setIsVBLoading] = useState(false);
  const [isVBSupported, setIsVBSupported] = useState(false);
  const localPeerVideoTrackID = useHMSStore(selectLocalVideoTrackID);
  const isVBPresent = useHMSStore(selectIsLocalVideoPluginPresent('HMSVB'));
  const isFeatureEnabled = useIsFeatureEnabled(FEATURE_LIST.VIDEO_PLUGINS);

  console.log('isVBPresent', isVBPresent);

  async function createPlugin() {
    if (!pluginRef.current) {
      const { HMSVBPlugin } = await import('@100mslive/hms-virtual-background');
      pluginRef.current = new HMSVBPlugin(
        HMSVirtualBackgroundTypes.NONE,
        HMSVirtualBackgroundTypes.NONE
      );
    }
  }

  useEffect(() => {
    if (!localPeerVideoTrackID) {
      return;
    }
    createPlugin().then(() => {
      //check support of plugin
      const pluginSupport = hmsActions.validateVideoPluginSupport(
        pluginRef.current
      );
      setIsVBSupported(pluginSupport.isSupported);
    });
  }, [hmsActions, localPeerVideoTrackID]);

  async function addPlugin() {
    console.log('addPlugin');
    setIsVBLoading(true);
    try {
      console.log('addPlugin 1');
      await createPlugin();
      console.log('addPlugin 2', pluginRef.current, window.HMS);
      if (window?.HMS?.virtualBackground)
        window.HMS.virtualBackground = pluginRef.current;
      console.log('addPlugin 3');
      const { background, backgroundType } = getRandomVirtualBackground();
      console.log('addPlugin 4');
      await pluginRef.current.setBackground(background, backgroundType);
      console.log('addPlugin 5');
      await hmsActions.addPluginToVideoTrack(
        pluginRef.current,
        Math.floor(role.publishParams.video.frameRate / 2)
      );
      console.log('addPlugin 6');
    } catch (err) {
      console.error('add virtual background plugin failed', err);
    }
    setIsVBLoading(false);
  }

  async function removePlugin() {
    console.log('addPlugin 7');
    if (pluginRef.current) {
      console.log('addPlugin 8');
      await hmsActions.removePluginFromVideoTrack(pluginRef.current);
      pluginRef.current = null;
    }
  }

  if (!isAllowedToPublish.video || !isVBSupported || !isFeatureEnabled) {
    return null;
  }

  return (
    <Tooltip
      title={
        isVBLoading
          ? 'Adding virtual background'
          : `Turn ${!isVBPresent ? 'on' : 'off'} virtual background`
      }
    >
      <Button
        disabled={isVBLoading}
        onClick={() => {
          !isVBPresent ? addPlugin() : removePlugin();
        }}
        data-testid="virtual_bg_btn"
        type={isVBPresent ? 'primary' : 'default'}
        loading={isVBLoading}
        shape="circle"
        icon={<RxShadow fontSize={20} />}
      />
    </Tooltip>
  );
};
