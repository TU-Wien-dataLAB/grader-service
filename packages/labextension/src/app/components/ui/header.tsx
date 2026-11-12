import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getCurrentUserQuery } from '../../../services/queries/users.queries';
import { HeaderIcons } from '../../../assets/header-icons';

export const Header = () => {
  const { data: user } = useQuery(getCurrentUserQuery());
  return (
    <div className={'flex self-stretch sticky bg-[#FAE2D5] h-29 p-6 items-end'}>
      <h1 className={'flex text-2xl font-bold'}>Hello, {user}</h1>
      <div className={'flex pr-15 items-start ml-auto'}>
        <HeaderIcons />
      </div>
    </div>
  );
};
