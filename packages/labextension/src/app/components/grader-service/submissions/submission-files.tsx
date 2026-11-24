import React from 'react';
import { BookIcon } from '../../../../assets/book-icon';
import { IFile, openInNewTab } from '../../../../services/local-file.service';
import { TSubmissionDirectory } from './submission-details-dialog';
import { CustomBadge } from '../../ui/badges';
import { useFileStatus } from './use-files-status-hook';

const ROW_GRID =
  'grid grid-cols-[minmax(0,15rem)_15rem_6rem_auto] items-center gap-x-6';

const FileLink = ({ file }: { file: IFile }) => {
  const { changed } = useFileStatus(file.path);
  return (
    <div
      onClick={() => openInNewTab(file.path)}
      className="flex min-w-0 items-center gap-2 cursor-pointer"
    >
      <BookIcon className="size-4 shrink-0" />
      <span className="truncate text-sm text-[#006699] underline underline-offset-2">
        {file.name}
      </span>
      {changed && <CustomBadge type="edited" />}
    </div>
  );
};
const FileRow = ({ file }: { file: IFile }) => (
  <div className={`${ROW_GRID} rounded-xs bg-white py-2 px-4`}>
    <FileLink file={file} />
  </div>
);

const FolderCard = ({ folder }: { folder: TSubmissionDirectory }) => (
  <div className="rounded-xs bg-white py-2 px-4">
    <p className="font-medium">{folder.name}</p>
    <ul className="mt-3 space-y-3">
      {folder.content.map(file => (
        <li key={file.path} className={ROW_GRID}>
          <div className="flex min-w-0 items-center gap-3">
            <span
              aria-hidden="true"
              className="ml-0.5 inline-block h-2.5 w-2.5 shrink-0 border-b-2 border-l-2 border-[#8D8D8D]"
            />
            <FileLink file={file} />
          </div>
          <span />
        </li>
      ))}
    </ul>
  </div>
);

interface ISubmissionFilesProps {
  files: (IFile | TSubmissionDirectory)[];
}

const SubmissionFiles = ({ files }: ISubmissionFilesProps) => {
  return (
    <div className="space-y-2">
      {files.map(item =>
        item.type === 'directory' ? (
          <FolderCard key={item.path} folder={item as TSubmissionDirectory} />
        ) : (
          <FileRow key={item.path} file={item} />
        )
      )}
    </div>
  );
};

export default SubmissionFiles;
