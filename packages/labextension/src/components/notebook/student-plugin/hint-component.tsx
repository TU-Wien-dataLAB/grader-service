import * as React from 'react';

export interface IHintComponentProps {
  hint: string;
  show: boolean;
}

export const HintComponent = (props: IHintComponentProps) => {
  if (!props.show) {
    return null;
  }

  return (
    <div className="mt-1 mb-1 rounded-md border border-blue-500/50 bg-blue-500/10 px-4 py-3 text-sm text-foreground">
      {props.hint}
    </div>
  );
};
