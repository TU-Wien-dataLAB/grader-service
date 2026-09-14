import { act, fireEvent, render, screen } from '@testing-library/react';

import { loadObject } from '../../../services/storage.service';
import { SearchField } from './search';
import React from 'react';

jest.mock('../../../services/storage.service', () => ({
  loadObject: jest.fn(),
  storeObject: jest.fn()
}));

const mockLoadObject = loadObject as jest.Mock;

const defaultProps = {
  recentSearchesKey: 'recent-searches',
  searchQuery: '',
  setSearchQuery: jest.fn()
};

beforeEach(() => {
  mockLoadObject.mockReturnValue([]);
});

describe('SearchField', () => {
  it('renders input with placeholder', () => {
    render(<SearchField {...defaultProps} placeholder="Search here" />);
    expect(screen.getByTestId('search-input')).toHaveAttribute(
      'placeholder',
      'Search here'
    );
  });

  it('shows recent searches on focus', async () => {
    mockLoadObject.mockReturnValue(['lecture1', 'lecture2']);
    render(<SearchField {...defaultProps} />);

    await act(async () => {
      fireEvent.focus(screen.getByTestId('search-input'));
      await new Promise(r => setTimeout(r, 50));
    });

    expect(await screen.findByText('lecture1')).toBeInTheDocument();
    expect(await screen.findByText('lecture2')).toBeInTheDocument();
  });
});
