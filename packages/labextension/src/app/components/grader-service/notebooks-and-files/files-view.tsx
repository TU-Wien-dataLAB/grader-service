import React from 'react';
import { SearchField } from '../../ui/search';
import { NewNotebookDialog } from './new-notebook-dialog';

export const FilesView = () => {
  const [searchQuery, setSearchQuery] = React.useState('');
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
        />
      </div>
    </div>
  );
};
