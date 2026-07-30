import React from 'react';
import { OctagonAlert } from 'lucide-react';

interface IErrorBannerProps {
  message: string;
}

export const ErrorBanner = (props: IErrorBannerProps) => {
  return (
    <div
      className="bg-[#FCE8EA] w-full flex flex-row border rounded-xs border-[#DC182C] p-4 gap-2 max-h-20"
      role="alert"
    >
      <OctagonAlert className={'fill-[#DC182C] text-[#FCE8EA] size-6'} />
      <div>
        <p className="font-medium">Error</p>
        <p className={'text-secondary-background'}>
          {props.message || 'Something went wrong. Please tyr again.'}
        </p>
      </div>
    </div>
  );
};
