import React from 'react';
import {FirstPersonDisplay} from '../FirstPersonDisplay';
import VideoList from '../VideoList';
import {useAppConfig} from '../../../AppData/useAppConfig';
import {useIsHeadless} from '../../../AppData/useUISettings';
import {useMediaQuery} from 'react-responsive';
import {StyledCenterView, StyledImage, StyledInnerContainer, StyledSidePaneContainer,} from './index.styled';
import {TabWidthQuery} from '@unpod/constants';

const MAX_TILES_FOR_MOBILE = 4;

/**
 * the below variables are for showing webinar etc. related image if required on certain meeting urls
 */
const webinarProps = JSON.parse(process.env.REACT_APP_WEBINAR_PROPS || '{}');
const eventRoomIDs = webinarProps?.ROOM_IDS || [];
const eventsImg = webinarProps?.IMAGE_FILE || ''; // the image to show in center
// the link to navigate to when user clicks on the image
const webinarInfoLink = webinarProps?.LINK_HREF || 'https://100ms.live/';

// The center of the screen shows bigger tiles
export const GridCenterView = ({peers, maxTileCount}) => {
  const limitMaxTiles = useMediaQuery(TabWidthQuery);
  const headlessConfig = useAppConfig('headlessConfig');
  const isHeadless = useIsHeadless();
  return (
    <StyledCenterView
      style={{
        marginInline:
          isHeadless && Number(headlessConfig?.tileOffset) === 0 ? 0 : 24,
      }}
    >
      {peers && peers.length > 0 ? (
        <VideoList
          peers={peers}
          maxTileCount={limitMaxTiles ? MAX_TILES_FOR_MOBILE : maxTileCount}
        />
      ) : eventRoomIDs.some((id) => window.location.href.includes(id)) ? (
        <div
          style={{
            display: 'grid',
            placeItems: 'center',
            height: '100%',
            width: '100%',
            padding: 24,
          }}
        >
          <a href={webinarInfoLink} target="_blank" rel="noreferrer">
            <StyledImage
              style={{padding: 8}}
              alt="Event template"
              src={eventsImg}
            />
          </a>
        </div>
      ) : (
        <FirstPersonDisplay/>
      )}
    </StyledCenterView>
  );
};

// Side pane shows smaller tiles
export const GridSidePaneView = ({peers}) => {
  const headlessConfig = useAppConfig('headlessConfig');
  const isHeadless = useIsHeadless();
  return (
    <StyledSidePaneContainer
      style={{
        marginInline:
          isHeadless && Number(headlessConfig?.tileOffset) === 0 ? '0' : '$8',
      }}
    >
      <StyledInnerContainer>
        {peers && peers.length > 0 && (
          <VideoList peers={peers} maxColCount={1}/>
        )}
      </StyledInnerContainer>
    </StyledSidePaneContainer>
  );
};
