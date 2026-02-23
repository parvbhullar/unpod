import React, {Fragment, useEffect, useState} from 'react';
import {selectLocalPeerID, useHMSStore, useVideoList,} from '@100mslive/react-sdk';
import ScreenshareTile from './ScreenshareTile';
import VideoTile from './VideoTile';
import useSortedPeers from '../../common/useSortedPeers';
import {useAppConfig} from '../../AppData/useAppConfig';
import {useIsHeadless, useUISettings} from '../../AppData/useUISettings';
import {UI_SETTINGS} from '../../common/constants';
import ThumbPagination from './ThumbPagination';
import {StyledRoot, StyledViewContainer} from './VideoList.styled';

const List = ({
                maxTileCount,
                peers,
                maxColCount,
                maxRowCount,
                includeScreenShareForPeer,
              }) => {
  const tileOffset = useAppConfig('headlessConfig', 'tileOffset');
  const isHeadless = useIsHeadless();
  const hideLocalVideo = useUISettings(UI_SETTINGS.hideLocalVideo);
  const localPeerId = useHMSStore(selectLocalPeerID);
  let sortedPeers = useSortedPeers({peers, maxTileCount});
  if (hideLocalVideo && sortedPeers.length > 1) {
    sortedPeers = filterPeerId(sortedPeers, localPeerId);
  }

  const count = peers.length || 4;
  const {ref, pagesWithTiles} = useVideoList({
    peers: sortedPeers,
    maxTileCount,
    maxColCount,
    maxRowCount, //: count / 2,
    includeScreenShareForPeer,
    aspectRatio: {width: 1, height: 1},
    offsetY: getOffset({isHeadless, tileOffset}),
  });

  const [page, setPage] = useState(0);
  useEffect(() => {
    // currentPageIndex should not exceed pages length
    if (page >= pagesWithTiles.length) {
      setPage(0);
    }
  }, [pagesWithTiles.length, page]);

  /*console.log(
    'pagesWithTiles: ',
    pagesWithTiles,
    { width: 1, height: 1 },
    ref.current?.clientWidth,
    ref.current?.clientHeight,
    maxTileCount,
    maxColCount,
    maxRowCount
  );*/

  return (
    <StyledRoot ref={ref}>
      <StyledViewContainer>
        {pagesWithTiles && pagesWithTiles.length > 0
          ? pagesWithTiles[page]?.map((tile) => {
            if (tile.width === 0 || tile.height === 0) {
              return null;
            }
            return (
              <Fragment key={tile.track?.id || tile.peer.id}>
                {tile.track?.source === 'screen' ? (
                  <ScreenshareTile
                    width={tile.width}
                    height={tile.height}
                    peerId={tile.peer.id}
                  />
                ) : (
                  <VideoTile
                    width={tile.width}
                    height={tile.height}
                    peerId={tile.peer?.id}
                    trackId={tile.track?.id}
                  />
                )}
              </Fragment>
            );
          })
          : null}
      </StyledViewContainer>

      {!isHeadless && pagesWithTiles.length > 1 ? (
        <ThumbPagination
          page={page}
          setPage={setPage}
          numPages={pagesWithTiles.length}
        />
      ) : null}
    </StyledRoot>
  );
};

const VideoList = React.memo(List);

/**
 * returns a new array of peers with the peer with peerId removed,
 * keeps the reference same if peer is not found
 */
function filterPeerId(peers, peerId) {
  const oldPeers = peers; // to keep the reference same if peer is not found
  let foundPeerToFilterOut = false;
  peers = [];
  for (let i = 0; i < oldPeers.length; i++) {
    if (oldPeers[i].id === peerId) {
      foundPeerToFilterOut = true;
    } else {
      peers.push(oldPeers[i]);
    }
  }
  if (!foundPeerToFilterOut) {
    peers = oldPeers;
  }
  return peers;
}

const getOffset = ({tileOffset, isHeadless}) => {
  if (!isHeadless || isNaN(Number(tileOffset))) {
    return 32;
  }
  return Number(tileOffset);
};

export default VideoList;
