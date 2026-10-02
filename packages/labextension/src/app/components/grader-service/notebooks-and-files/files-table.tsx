import React, { useMemo } from 'react';
import {
  DataTableColumnDef,
  expanderColumn,
  INDENT_STEP,
  NestedTable,
  selectColumn
} from '../../ui/nested-table/nested-table';
import { getDate } from '../../utils/utils';
import { OnChangeFn, RowSelectionState } from '@tanstack/react-table';
import { IFile, openInNewTab } from '../../../../services/local-file.service';
import { Eye, Pencil } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { selectedDirQuery } from '../../../../services/queries/files.queries';
import { Button } from '../../../shadcn-components/ui/button';

export type FileRow = {
  id: string;
  path: string;
  name: string; // should be presented on parents and children so search matches every row
  type: string;
  size: number;
  last_modified?: string; // only present on children
  actions?: boolean;
  subRows?: Array<FileRow>;
};

type TTableProps = {
  files: IFile[];
  search?: string;
  setSearch: (val: string) => void;
  rowSelection: RowSelectionState;
  onRowSelectionChange: OnChangeFn<RowSelectionState>;
};

export const FilesDataTable = (props: TTableProps) => {
  const { files, search, rowSelection, onRowSelectionChange, setSearch } =
    props;

  const { data: selectedDir } = useQuery(selectedDirQuery());

  const handleOpenFile = async (filePath: string) => {
    // TODO: open file in read-only mode when in release dir
    await openInNewTab(filePath);
  };

  const columns = useMemo<Array<DataTableColumnDef<FileRow>>>(
    () => [
      expanderColumn<FileRow>(),
      selectColumn<FileRow>(),
      {
        accessorKey: 'name',
        header: 'Name',
        cell: ({ row, getValue }) => (
          <div style={{ paddingLeft: row.depth * INDENT_STEP }}>
            {getValue<string>()}
          </div>
        )
      },
      {
        accessorKey: 'last_modified',
        header: 'Last saved on',
        enableGlobalFilter: false,
        cell: ({ getValue, row }) => {
          const last_modified = getValue<string | undefined>();
          const date =
            last_modified === undefined
              ? undefined
              : getDate(new Date(last_modified));
          return (
            row.original.type !== 'directory' && date && <span>{date}</span>
          );
        }
      },
      {
        accessorKey: 'type',
        header: 'File type',
        enableGlobalFilter: true,
        filterFn: 'filterFn_equalsString',
        cell: ({ row }) => <span>{row.original.type}</span>
      },
      {
        accessorKey: 'size',
        header: 'File size',
        enableGlobalFilter: false,
        cell: ({ row }) => <span>{row.original.size?.toFixed(2)} B</span>
      },
      {
        id: 'actions',
        header: selectedDir === 'source' ? 'Edit' : 'View',
        enableGlobalFilter: false,
        cell: ({ row }) => {
          return (
            row.original.type !== 'directory' && (
              <Button
                variant={'link'}
                onClick={() => handleOpenFile(row.original.path)}
              >
                {selectedDir === 'source' ? (
                  <Pencil className={'size-5 fill-primary text-card!'} />
                ) : (
                  <Eye className={'size-5 fill-primary text-card!'} />
                )}
              </Button>
            )
          );
        }
      }
    ],
    [selectedDir]
  );

  // prepare table data
  const generateData = (files?: IFile[]): FileRow[] =>
    (files ?? []).map(file => ({
      id: file.path,
      path: file.path,
      name: file.name,
      type: file.type,
      last_modified: file.last_modified,
      size: file.size,
      subRows: file.type === 'directory' ? generateData(file.content) : []
    }));

  const data = useMemo(() => generateData(files), [files]);
  return (
    <NestedTable
      columns={columns}
      data={data}
      getSubRows={row => row.subRows}
      getRowId={row => row.id}
      globalFilter={search}
      onGlobalFilterChange={setSearch}
      rowSelection={rowSelection}
      onRowSelectionChange={onRowSelectionChange}
    />
  );
};
