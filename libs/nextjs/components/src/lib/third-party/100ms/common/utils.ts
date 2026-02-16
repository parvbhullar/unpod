import { QUERY_PARAM_SKIP_PREVIEW } from './constants';

export function shadeColor(color, percent) {
  let R = parseInt(color.substring(1, 3), 16);
  let G = parseInt(color.substring(3, 5), 16);
  let B = parseInt(color.substring(5, 7), 16);

  R = Math.floor((R * (100 + percent)) / 100);
  G = Math.floor((G * (100 + percent)) / 100);
  B = Math.floor((B * (100 + percent)) / 100);

  R = R < 255 ? R : 255;
  G = G < 255 ? G : 255;
  B = B < 255 ? B : 255;

  const RR =
    R.toString(16).length === 1 ? '0' + R.toString(16) : R.toString(16);
  const GG =
    G.toString(16).length === 1 ? '0' + G.toString(16) : G.toString(16);
  const BB =
    B.toString(16).length === 1 ? '0' + B.toString(16) : B.toString(16);

  return '#' + RR + GG + BB;
}

/**
 * TODO: this is currently an O(N**2) function, don't use with peer lists, it's currently
 * being used to find intersection between list of role names where the complexity shouldn't matter much.
 */
export const arrayIntersection = (a, b) => {
  if (a === undefined || b === undefined) {
    return [];
  }
  // ensure "a" is the bigger array
  if (b.length > a.length) {
    let t = b;
    b = a;
    a = t;
  }
  return a.filter(function (e) {
    return b.indexOf(e) > -1;
  });
};

export const getMetadata = (metadataString) => {
  try {
    return metadataString === '' ? {} : JSON.parse(metadataString);
  } catch (error) {
    return {};
  }
};

export const metadataProps = function (peer) {
  return {
    isHandRaised: getMetadata(peer.metadata)?.isHandRaised,
  };
};

export const isScreenshareSupported = () => {
  return typeof navigator.mediaDevices.getDisplayMedia !== 'undefined';
};

export const getDefaultMeetingUrl = () => {
  return (
    window.location.href.replace('meeting', 'preview') +
    `?${QUERY_PARAM_SKIP_PREVIEW}=true`
  );
};

export const getRoutePrefix = () => {
  return window.location.pathname.startsWith('/streaming') ? '/streaming' : '';
};

export const isStreamingKit = () => {
  return window.location.pathname.startsWith('/streaming');
};

export const isInternalRole = (role) => role && role.startsWith('__internal');
const PEER_NAME_PLACEHOLDER = 'peerName';
const labelMap = new Map([
  [[true, 'screen'].toString(), 'Your Screen'],
  [[true, 'regular'].toString(), `You (${PEER_NAME_PLACEHOLDER})`],
  [[false, 'screen'].toString(), `${PEER_NAME_PLACEHOLDER}'s Screen`],
  [[false, 'regular'].toString(), PEER_NAME_PLACEHOLDER],
  [[true, undefined].toString(), `You (${PEER_NAME_PLACEHOLDER})`],
  [[false, undefined].toString(), `${PEER_NAME_PLACEHOLDER}`],
]);

export const metadataPayloadParser = (payload) => {
  try {
    const data = window.atob(payload);
    const parsedData = JSON.parse(data);
    return parsedData;
  } catch (e) {
    return { payload };
  }
};

export const getVideoTileLabel = ({ peerName, isLocal, track }) => {
  const isPeerPresent = peerName !== undefined;
  if (!isPeerPresent || !track) {
    // for peers with only audio track
    return isPeerPresent
      ? labelMap
          .get([isLocal, undefined].toString())
          .replace(PEER_NAME_PLACEHOLDER, peerName)
      : '';
  }
  const isLocallyMuted = track.volume === 0;
  // Map [isLocal, videoSource] to the label to be displayed.
  let label = labelMap.get([isLocal, track.source].toString());
  if (label) {
    label = label.replace(PEER_NAME_PLACEHOLDER, peerName);
  } else {
    label = `${peerName} ${track.source}`;
  }
  label = `${label}${track.degraded ? '(Degraded)' : ''}`;
  return `${label}${isLocallyMuted ? ' (Muted for you)' : ''}`;
};

function canPublishAV(role) {
  const params = role?.publishParams;
  if (params?.allowed) {
    return params.allowed.includes('video') || params.allowed.includes('audio');
  }
  return false;
}

export const normalizeAppPolicyConfig = (
  roleNames,
  rolesMap,
  appPolicyConfig = {}
) => {
  const newConfig = Object.assign({}, appPolicyConfig);
  roleNames.forEach((roleName) => {
    if (!newConfig[roleName]) {
      newConfig[roleName] = {};
    }
    const subscribedRoles =
      rolesMap[roleName].subscribeParams?.subscribeToRoles || [];

    const isNotSubscribingOrSubscribingToSelf =
      subscribedRoles.length === 0 ||
      (subscribedRoles.length === 1 && subscribedRoles[0] === roleName);
    if (!newConfig[roleName].center) {
      const publishingRoleNames = roleNames.filter(
        (roleName) =>
          canPublishAV(rolesMap[roleName]) && subscribedRoles.includes(roleName)
      );
      if (isNotSubscribingOrSubscribingToSelf) {
        newConfig[roleName].center = [roleName];
      } else {
        // all other publishing roles apart from local role in center by default
        newConfig[roleName].center = publishingRoleNames.filter(
          (rName) => rName !== roleName
        );
      }
    }
    // everyone from my role is in sidepane by default if they can publish
    if (!newConfig[roleName].sidepane) {
      if (isNotSubscribingOrSubscribingToSelf) {
        newConfig[roleName].sidepane = [];
      } else {
        newConfig[roleName].sidepane = canPublishAV(rolesMap[roleName])
          ? [roleName]
          : [];
      }
    }
    if (!newConfig[roleName].selfRoleChangeTo) {
      newConfig[roleName].selfRoleChangeTo = roleNames;
    }
    if (!newConfig[roleName].remoteRoleChangeFor) {
      newConfig[roleName].remoteRoleChangeFor = roleNames;
    }
  });

  return newConfig;
};
