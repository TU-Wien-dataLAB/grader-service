import React from 'react';

interface IEmptyStateProps {
  icon?: React.ReactElement;
  title: string;
  description?: string;
}

export const EmptyState = (props: IEmptyStateProps) => {
  return (
    <div className={'flex flex-col p-6 items-center gap-4 self-stretch'}>
      {props.icon}
      <div className={'flex flex-col items-center gap-2'}>
        <h2 className={'text-xl font-bold'}>{props.title}</h2>
        <p className={'text-center text-sm'}>{props.description}</p>
      </div>
    </div>
  );
};
