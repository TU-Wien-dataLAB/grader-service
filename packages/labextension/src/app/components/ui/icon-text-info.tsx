import React from 'react';

export interface IIconTextInfo {
  icon: JSX.Element;
  text: string;
}

export const IconTextInfo = (props: IIconTextInfo) => {
  return (
    <div className={'flex flex-row gap-2'}>
      {props.icon}
      <h1 className={'text-lg'}>{props.text}</h1>
    </div>
  );
};
