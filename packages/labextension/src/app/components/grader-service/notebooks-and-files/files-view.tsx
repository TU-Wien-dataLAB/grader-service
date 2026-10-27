import React, { useEffect, useMemo, useState } from 'react';
import { SearchField } from '../../ui/search';
import { NewNotebookDialog } from './new-notebook-dialog';
import { useQuery } from '@tanstack/react-query';
import { lectureQuery } from '../../../../services/queries/lectures.queries';
import { selectedDirQuery } from '../../../../services/queries/files.queries';
import {
  getFiles,
  lectureBasePath,
  openInFileBrowser
} from '../../../../services/local-file.service';
import { Eye, Pencil } from 'lucide-react';
import { GlobalObjects } from '../../../../index';
import { Contents } from '@jupyterlab/services';
import { FilterFilesButton } from '../../ui/filter-button';
import {
  ToggleGroup,
  ToggleGroupItem
} from '../../../shadcn-components/ui/toggle-group';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { useAssignmentGenerateReleaseVer } from '../../../hooks/assignment/assignment-generate-release-ver';
import { storeString } from '../../../../services/storage.service';
import { queryClient, useMutationStatus } from '../../../../widget';
import { SuccessBanner } from '../../ui/success-banner';
import { ErrorBanner } from '../../ui/error-banner';
import { EmptyState } from '../../utils/empty-state';
import { EmptyDirIcon } from '../../../../assets/empty-dir-icon';
import { FilesDataTable } from './files-table';
import { ColumnFiltersState, RowSelectionState } from '@tanstack/react-table';
import { Button } from '../../../shadcn-components/ui/button';
import { getRemoteStatus } from '../../../../services/git.service';
import { RepoType } from '../../utils/repo-type';
import { SaveFilesDialog } from './save-files-dialog';
import { Badge } from '../../../shadcn-components/ui/badge';
import { LoadUpdatesDialog } from './load-updates-dialog';

interface IFilesViewProps {
  lectureId: number;
  assignmentId: number;
}

export const FilesView = (props: IFilesViewProps) => {
  const { status } = useMutationStatus();
  const { data: selectedDir } = useQuery(
    selectedDirQuery(props.lectureId, props.assignmentId)
  );
  const { data: lecture } = useQuery(lectureQuery(props.lectureId));
  const { data: files = [] } = useQuery({
    queryKey: ['files', lecture?.code, props.assignmentId, selectedDir],
    queryFn: async () => {
      return await getFiles(srcPath);
    }
  });
  const { data: remoteRepoStatus } = useQuery({
    queryKey: [
      'remote-repo-status',
      lecture?.code,
      props.assignmentId,
      selectedDir
    ],
    queryFn: async () => {
      return await getRemoteStatus(
        props.lectureId,
        props.assignmentId,
        selectedDir === 'source' ? RepoType.SOURCE : RepoType.RELEASE
      );
    },
    enabled: !!files
  });

  const handleDirSwitch = async (dir: string) => {
    if (dir === selectedDir) {
      return;
    }
    if (dir === 'release') {
      handleGenerateAssignmentReleaseVer(lecture.id, props.assignmentId);
    }
    // set new dir
    storeString(
      `${props.lectureId}:${props.assignmentId}:files-selected-dir`,
      dir
    );
    const newSrcPath = `${lectureBasePath}${lecture.code}/${dir}/${props.assignmentId}`;
    await queryClient
      .invalidateQueries({
        queryKey: ['selectedDir', props.lectureId, props.assignmentId]
      })
      .then(() => openInFileBrowser(newSrcPath));
  };

  const srcPath = useMemo(
    () =>
      `${lectureBasePath}${lecture?.code}/${selectedDir}/${props.assignmentId}`,
    [lecture?.code, selectedDir, props.assignmentId]
  );

  // synchronize files shown in app with jupyterlab's file browser
  useEffect(() => {
    const handler = async (
      sender: Contents.IManager,
      change: Contents.IChangedArgs
    ) => {
      const { oldValue, newValue } = change;
      if (
        (newValue && !newValue.path.includes(srcPath)) ||
        (oldValue && !oldValue.path.includes(srcPath))
      ) {
        return;
      }
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['files', lecture.code, props.assignmentId, selectedDir]
        }),
        queryClient.invalidateQueries({
          queryKey: [
            'remote-repo-status',
            lecture?.code,
            props.assignmentId,
            selectedDir
          ]
        })
      ]);
    };

    GlobalObjects.docManager.services.contents.fileChanged.connect(handler);
    return () => {
      GlobalObjects.docManager.services.contents.fileChanged.disconnect(
        handler
      );
    };
  }, [srcPath, files]);

  const fileTypes = useMemo(() => {
    return [...new Set(files?.map(file => file.type))];
  }, [files]);
  const { handleGenerateAssignmentReleaseVer } =
    useAssignmentGenerateReleaseVer();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [checkedFileTypes, setCheckedFileTypes] = React.useState<string[]>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [openSaveFilesDialog, setOpenSaveFilesDialog] = useState(false);
  const [openPullAssignmentDialog, setOpenPullAssignmentDialog] =
    useState(false);
  const columnFilters = useMemo<ColumnFiltersState>(
    () => [
      ...(searchQuery ? [{ id: 'name', value: searchQuery }] : []),
      ...(checkedFileTypes.length
        ? [{ id: 'type', value: checkedFileTypes }]
        : [])
    ],
    [searchQuery, checkedFileTypes]
  );
  const remoteStatusBadge = () => {
    switch (remoteRepoStatus?.status) {
      case 'UP_TO_DATE':
        return <Badge className={'bg-lime-600'}>No updates available</Badge>;
      case 'PULL_NEEDED':
        return <Badge className={'bg-red-400'}>Updates available</Badge>;
      case 'PUSH_NEEDED':
        return <Badge className={'bg-yellow-600'}>Unsaved changes</Badge>;
      case 'DIVERGENT':
        return <Badge className={'bg-red-700'}>Out of sync</Badge>;
      case 'NO_REMOTE_REPO':
        return <Badge className={'bg-gray-400'}>Not backed up</Badge>;
    }
  };
  return (
    <div className={'flex flex-col items-start gap-4 self-stretch h-full'}>
      {files?.length <= 0 ? (
        <div className={'flex flex-col items-center self-stretch'}>
          <EmptyState
            icon={<EmptyDirIcon />}
            title={'Get started with your first notebook'}
            description={
              'Currently, there is no notebook available. You can create a new one now.'
            }
          />
          <NewNotebookDialog
            assignmentId={props.assignmentId}
            lectureCode={lecture?.code}
          />
        </div>
      ) : (
        <>
          <div
            className={'flex justify-between items-center self-stretch gap-2'}
          >
            <h2 className={'text-xl font-bold'}>Notebooks & files</h2>
            {remoteStatusBadge() ?? null}
            <NewNotebookDialog
              assignmentId={props.assignmentId}
              lectureCode={lecture?.code}
              buttonVariant={'outline'}
            />
          </div>
          {status.status === 'success' && (
            <SuccessBanner message={status.message} />
          )}
          {status.status === 'error' && (
            <ErrorBanner message={status.message} />
          )}
          <div className={'flex justify-between items-center self-stretch'}>
            <SearchField
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              placeholder={'Search for notebooks & files'}
            />
            <div className={'flex gap-4 items-center ml-auto'}>
              <FilterFilesButton
                allFileTypes={fileTypes}
                checkedFileTypes={checkedFileTypes}
                setFileTypes={setCheckedFileTypes}
              />
              <ToggleGroup
                type={'single'}
                value={selectedDir}
                onValueChange={dir => handleDirSwitch(dir)}
              >
                <Tooltip>
                  <TooltipTrigger
                    render={
                      <span>
                        <ToggleGroupItem
                          value={'source'}
                          disabled={selectedDir === 'source'}
                          variant={
                            selectedDir === 'source' ? 'default' : 'outline'
                          }
                        >
                          <Pencil className={'size-4'} />
                        </ToggleGroupItem>
                      </span>
                    }
                  />
                  <TooltipContent>
                    <p>Instructor View</p>
                  </TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger
                    render={
                      <span>
                        <ToggleGroupItem
                          value={'release'}
                          disabled={selectedDir === 'release'}
                          variant={
                            selectedDir === 'release' ? 'default' : 'outline'
                          }
                        >
                          <Eye className={'size-4'} />
                        </ToggleGroupItem>
                      </span>
                    }
                  />
                  <TooltipContent>
                    <p>Student Preview</p>
                  </TooltipContent>
                </Tooltip>
              </ToggleGroup>
            </div>
          </div>
          <FilesDataTable
            files={files}
            rowSelection={rowSelection}
            onRowSelectionChange={setRowSelection}
            columnFilters={columnFilters}
            lectureId={props.lectureId}
            assignmentId={props.assignmentId}
          />
          <div className={'flex items-center gap-4 self-stretch'}>
            <Button onClick={() => setOpenSaveFilesDialog(true)}>Save</Button>
            <Button
              variant={'outline'}
              onClick={() => setOpenPullAssignmentDialog(true)}
            >
              Load updates
            </Button>
          </div>
        </>
      )}
      {openSaveFilesDialog && (
        <SaveFilesDialog
          files={files}
          isOpen={openSaveFilesDialog}
          setIsOpen={setOpenSaveFilesDialog}
          selectedRows={rowSelection}
          lecture={lecture}
          assignmentId={props.assignmentId}
          selectedDir={selectedDir}
        />
      )}
      {openPullAssignmentDialog && (
        <LoadUpdatesDialog
          lecture={lecture}
          assignmentId={props.assignmentId}
          selectedDir={selectedDir}
          isOpen={openPullAssignmentDialog}
          setIsOpen={setOpenPullAssignmentDialog}
        />
      )}
    </div>
  );
};
