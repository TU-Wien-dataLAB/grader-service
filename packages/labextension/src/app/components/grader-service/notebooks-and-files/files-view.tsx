import React, { useEffect, useMemo } from 'react';
import { SearchField } from '../../ui/search';
import { NewNotebookDialog } from './new-notebook-dialog';
import { useQuery } from '@tanstack/react-query';
import { lectureQuery } from '../../../../services/queries/lectures.queries';
import { assignmentQuery } from '../../../../services/queries/assignments.queries';
import { selectedDirQuery } from '../../../../services/queries/files.queries';
import {
  getFiles,
  lectureBasePath
} from '../../../../services/local-file.service';
import { Pencil } from 'lucide-react';
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

interface IFilesViewProps {
  lectureId: number;
  assignmentId: number;
}

export const FilesView = (props: IFilesViewProps) => {
  const { data: selectedDir } = useQuery(selectedDirQuery());
  const { data: lecture } = useQuery(lectureQuery(props.lectureId));
  const { data: assignment } = useQuery(
    assignmentQuery(props.lectureId, props.assignmentId)
  );

  const { data: files = [], refetch: refetchFiles } = useQuery({
    queryKey: ['files', lecture.id, assignment.id, selectedDir],
    queryFn: async () => {
      const path = `${lectureBasePath}${lecture.code}/${selectedDir}/${assignment.id}`;
      return await getFiles(path);
    }
  });

  useEffect(() => {
    const srcPath = `${lectureBasePath}${lecture.code}/source/${assignment.id}`;
    GlobalObjects.docManager.services.contents.fileChanged.connect(
      async (sender: Contents.IManager, change: Contents.IChangedArgs) => {
        const { oldValue, newValue } = change;
        if (
          (newValue && !newValue.path.includes(srcPath)) ||
          (oldValue && !oldValue.path.includes(srcPath))
        ) {
          return;
        }
        await refetchFiles();
      }
    );
  }, [assignment, lecture]);

  const [searchQuery, setSearchQuery] = React.useState('');

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
    return result;
  }, [searchQuery, files]);
  return (
    <div className={'flex flex-col items-start gap-4 self-stretch'}>
      <div className={'flex justify-between items-center self-stretch'}>
        <h2 className={'text-xl font-bold'}>Notebooks & files</h2>
        <NewNotebookDialog />
      </div>
      <div className={'flex justify-between items-center self-stretch'}>
        <SearchField
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          placeholder={'Search for notebooks & files'}
        />
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Last saved on</TableHead>
            <TableHead>File type</TableHead>
            <TableHead>File size</TableHead>
            <TableHead>Edit</TableHead>
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
                  <Pencil className={'size-5 fill-primary text-card!'} />
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};
