import React from 'react';
import { CircleCheck } from 'lucide-react';

interface ISuccessBannerProps {
  message: string;
}

export const SuccessBanner = (props: ISuccessBannerProps) => {
  return (
    <div
      className="bg-[#E9F5D2] flex flex-row w-full border rounded-xs border-[#6A9816] p-4 gap-2 max-h-20"
      role="alert"
    >
      <CircleCheck className={'fill-[#6A9816] size-6'} />
      <div>
        <p className="font-medium">Success</p>
        <p className={'text-secondary-background'}>{props.message}</p>
      </div>
    </div>
  );
};
