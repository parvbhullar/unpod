import { serverFetcher } from '../../../../lib/fetcher';
import type { Pilot, Spaces } from '@unpod/constants/types';

type HeaderProps = {
  removeHeader?: boolean;
  isListingPage: boolean;
  space?: Spaces;
};

type PilotProps = {
  space: Spaces | null;
  isPublicView: boolean;
  headerProps: HeaderProps;
  pilot_status: string;
  pilot: Pilot | null;
};

export async function getPilot(pilotSlug: string): Promise<PilotProps> {
  const props: PilotProps = {
    space: null,
    isPublicView: true,
    headerProps: {
      isListingPage: true,
    },
    pilot_status: '',
    pilot: null,
  };
  try {
    props.pilot = (await serverFetcher(`core/pilots/${pilotSlug}/`)) as Pilot;
    return props;
  } catch (error) {
    console.log('error: ', error);
  }
  return props;
}

export async function getSpace(spaceSlug: string): Promise<{
  space: Spaces | null;
  isPublicView: boolean;
  headerProps: HeaderProps;
}> {
  const props: {
    space: Spaces | null;
    isPublicView: boolean;
    headerProps: HeaderProps;
  } = {
    space: null,
    isPublicView: true,
    headerProps: {
      removeHeader: false,
      isListingPage: true,
    },
  };
  try {
    const space = (await serverFetcher(`spaces/${spaceSlug}/`)) as Spaces;
    props.space = space;
    props.headerProps = {
      ...props.headerProps,
      space,
      isListingPage: space.space_type === 'general',
    };
    return props;
  } catch (error) {
    console.log('error: ', error);
  }
  return props;
}
