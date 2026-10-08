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
import { useMutationStatus } from '../../../../widget';
import { SuccessBanner } from '../../ui/success-banner';
import { ErrorBanner } from '../../ui/error-banner';
import { EmptyState } from '../../utils/empty-state';
import { EmptyDirIcon } from '../../../../assets/empty-dir-icon';
import { FilesDataTable } from './files-table';
import { ColumnFiltersState, RowSelectionState } from '@tanstack/react-table';
import { Button } from '../../../shadcn-components/ui/button';
import { pullAssignment } from '../../../../services/git.service';
import { RepoType } from '../../utils/repo-type';
import { HTTPError } from '../../../../services/request.service';
import { SaveFilesDialog } from './save-files-dialog';

interface IFilesViewProps {
  lectureId: number;
  assignmentId: number;
}

export const FilesView = (props: IFilesViewProps) => {
  const { status, setStatus } = useMutationStatus();
  const { data: selectedDir, refetch: refetchSelectedDir } =
    useQuery(selectedDirQuery());
  const { data: lecture } = useQuery(lectureQuery(props.lectureId));
  const { data: files = [], refetch: refetchFiles } = useQuery({
    queryKey: ['files', lecture.code, props.assignmentId, selectedDir],
    queryFn: async () => {
      return await getFiles(srcPath);
    }
  });
  const handlePullAssignment = async () => {
    try {
      await Promise.all([
        pullAssignment(lecture.id, props.assignmentId, RepoType.SOURCE),
        refetchFiles()
      ]).catch((err: HTTPError) =>
        setStatus({ message: err.message, status: 'error' })
      );
    } catch (err) {
      setStatus({ message: 'Failed to update assignment!', status: 'error' });
    }
  };
  const handleDirSwitch = async (dir: string) => {
    if (dir === selectedDir) {
      return;
    }
    if (dir === 'release') {
      handleGenerateAssignmentReleaseVer(lecture.id, props.assignmentId);
    }
    // set new dir
    storeString('files-selected-dir', dir);
    const newSrcPath = `${lectureBasePath}${lecture.code}/${dir}/${props.assignmentId}`;
    refetchSelectedDir().then(() => openInFileBrowser(newSrcPath));
  };

  const srcPath = useMemo(
    () =>
      `${lectureBasePath}${lecture.code}/${selectedDir}/${props.assignmentId}`,
    [lecture.code, selectedDir, props.assignmentId]
  );

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
      await refetchFiles();
    };

    GlobalObjects.docManager.services.contents.fileChanged.connect(handler);
    return () => {
      GlobalObjects.docManager.services.contents.fileChanged.disconnect(
        handler
      );
    };
  }, [srcPath, refetchFiles]);
  const [searchQuery, setSearchQuery] = React.useState('');

  const [checkedFileTypes, setCheckedFileTypes] = React.useState<string[]>([]);

  const fileTypes = useMemo(() => {
    return [...new Set(files?.map(file => file.type))];
  }, [files]);
  const columnFilters = useMemo<ColumnFiltersState>(
    () => [
      ...(searchQuery ? [{ id: 'name', value: searchQuery }] : []),
      ...(checkedFileTypes.length
        ? [{ id: 'type', value: checkedFileTypes }]
        : [])
    ],
    [searchQuery, checkedFileTypes]
  );
  const { handleGenerateAssignmentReleaseVer } =
    useAssignmentGenerateReleaseVer();
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [openSaveFilesDialog, setOpenSaveFilesDialog] = useState(false);
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
            lectureCode={lecture.code}
          />
        </div>
      ) : (
        <>
          <div className={'flex justify-between items-center self-stretch'}>
            <h2 className={'text-xl font-bold'}>Notebooks & files</h2>
            <NewNotebookDialog
              assignmentId={props.assignmentId}
              lectureCode={lecture.code}
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
          />
          <div className={'flex items-center gap-4 self-stretch'}>
            <Button onClick={() => setOpenSaveFilesDialog(true)}>Save</Button>
            <Button variant={'outline'} onClick={() => handlePullAssignment()}>
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
          refetchFiles={refetchFiles}
        />
      )}
    </div>
  );
};
