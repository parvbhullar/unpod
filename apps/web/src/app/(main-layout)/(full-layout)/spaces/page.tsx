import { AppSpaceRoot } from '../../../../modules/AppSpaceMod';
import type { ComponentType } from 'react';

const pageTitle = 'Spaces';

export const metadata = {
  title: pageTitle,
};

export default function SpaceSlugPage() {
  const AppSpaceRootAny = ((
    AppSpaceRoot as unknown as { default?: ComponentType<any> }
  ).default ?? AppSpaceRoot) as ComponentType<any>;
  return <AppSpaceRootAny pageTitle={pageTitle} />;
}
