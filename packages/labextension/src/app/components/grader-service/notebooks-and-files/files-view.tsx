import React, { useEffect, useMemo } from 'react';
import { SearchField } from '../../ui/search';
import { NewNotebookDialog } from './new-notebook-dialog';
import { useQuery } from '@tanstack/react-query';
import { lectureQuery } from '../../../../services/queries/lectures.queries';
import { selectedDirQuery } from '../../../../services/queries/files.queries';
import {
  getFiles,
  IFile,
  lectureBasePath,
  openInFileBrowser,
  openInNewTab
} from '../../../../services/local-file.service';
import { Eye, Pencil } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '../../../shadcn-components/ui/table';
import { GlobalObjects } from '../../../../index';
import { Contents } from '@jupyterlab/services';
import { getDate } from '../../utils/utils';
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
import { Button } from '../../../shadcn-components/ui/button';

interface IFilesViewProps {
  lectureId: number;
  assignmentId: number;
}

export const FilesView = (props: IFilesViewProps) => {
  const { data: selectedDir, refetch: refetchSelectedDir } =
    useQuery(selectedDirQuery());
  const { data: lecture } = useQuery(lectureQuery(props.lectureId));
  const { status } = useMutationStatus();

  const srcPath = useMemo(
    () =>
      `${lectureBasePath}${lecture.code}/${selectedDir}/${props.assignmentId}`,
    [lecture.code, selectedDir, props.assignmentId]
  );
  const { data: files = [], refetch: refetchFiles } = useQuery({
    queryKey: ['files', lecture.code, props.assignmentId, selectedDir],
    queryFn: async () => {
      return await getFiles(srcPath);
    }
  });

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

  const filteredFiles = useMemo(() => {
    let result = files;
    if (!files) {
      return [];
    }

    if (searchQuery) {
      result = files.filter(file =>
        file.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    if (checkedFileTypes?.length > 0) {
      result = result.filter(file => checkedFileTypes.includes(file.type));
    }
    return result;
  }, [searchQuery, checkedFileTypes, files]);
  const fileTypes = useMemo(() => {
    return [...new Set(files?.map(file => file.type))];
  }, [files]);

  const { handleGenerateAssignmentReleaseVer } =
    useAssignmentGenerateReleaseVer();
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

  const handleOpenFile = async (file: IFile) => {
    // TODO: open file in read-only mode when in release dir
    await openInNewTab(`${file.path}`);
  };

  return (
    <div className={'flex flex-col items-start gap-4 self-stretch h-full'}>
      <div className={'flex justify-between items-center self-stretch'}>
        <h2 className={'text-xl font-bold'}>Notebooks & files</h2>
        <NewNotebookDialog
          assignmentId={props.assignmentId}
          lectureCode={lecture.code}
        />
      </div>
      {status.status === 'success' && (
        <SuccessBanner message={status.message} />
      )}
      {status.status === 'error' && <ErrorBanner message={status.message} />}
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
                      variant={selectedDir === 'source' ? 'default' : 'outline'}
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
      <Table>
        <TableHeader className={'sticky top-0 bg-card'}>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Last saved on</TableHead>
            <TableHead>File type</TableHead>
            <TableHead>File size</TableHead>
            <TableHead>{selectedDir === 'source' ? 'Edit' : 'View'}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredFiles?.map(file => (
            <TableRow key={file.name}>
              <TableCell>{file.name}</TableCell>
              <TableCell>{getDate(new Date(file.last_modified))}</TableCell>
              <TableCell>{file.type}</TableCell>
              <TableCell>{file.size} B</TableCell>
              <TableCell>
                {file.type !== 'directory' && (
                  <Button variant={'link'} onClick={() => handleOpenFile(file)}>
                    {selectedDir === 'source' ? (
                      <Pencil className={'size-5 fill-primary text-card!'} />
                    ) : (
                      <Eye className={'size-5 fill-primary text-card!'} />
                    )}
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};
