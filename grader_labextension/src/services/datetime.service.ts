// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import moment from 'moment';

// 2021-09-03T11:57
export function localToUTC(time: string): string {
  return moment(time).utc().format('YYYY-MM-DDTHH:mm:ss.sss') + 'Z';
}

export function utcToLocal(time: string): string {
  return moment.utc(time).local().format('YYYY-MM-DDTHH:mm:ss.sss');
}

export function utcToLocalFormat(time: string): string {
  const locale = window.navigator.language;
  const localeData = moment.localeData(locale);
  const format = localeData.longDateFormat('L') + ' HH:mm:ss';
  return moment.utc(time).local().format(format);
}

export function utcToTimestamp(time: string): number {
  return moment(time, 'YYYY-MM-DDTHH:mm:ss.sss').valueOf();
}
