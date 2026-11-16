import {
  NoFilesBadge,
  OutOfSyncBadge,
  UnsavedChangesBadge,
  UpdatesAvailableBadge
} from '../../../ui/badges';
import { RemoteFileStatus } from '../../../../../model/remoteFileStatus';
import React from 'react';

interface IAssignmentReleaseRemoteStatusBadgeProps {
  remoteRepoStatus: RemoteFileStatus | undefined;
  filesLength: number | undefined;
}

export const AssignmentReleaseRemoteStatusBadge = (
  props: IAssignmentReleaseRemoteStatusBadgeProps
) => {
  if (props.filesLength === 0) {
    return <NoFilesBadge />;
  }
  switch (props.remoteRepoStatus) {
    case RemoteFileStatus.UpdateNeeded:
      return <UpdatesAvailableBadge />;
    case RemoteFileStatus.UnsavedChanges:
      return <UnsavedChangesBadge />;
    case RemoteFileStatus.Divergent:
      return <OutOfSyncBadge />;
  }
};
