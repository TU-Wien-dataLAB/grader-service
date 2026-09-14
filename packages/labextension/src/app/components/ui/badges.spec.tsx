import React from 'react';
import { render, screen } from '@testing-library/react';
import {
  AutomaticGradingBadge,
  CompletedAssignmentBadge,
  CreatedAssignmentBadge,
  FullyAutomaticGradingBadge,
  ManualGradingBadge,
  ReleasedAssignmentBadge
} from './badges';

describe('Badge', () => {
  it('renders FullyAutomaticGradingBadge with correct text', () => {
    render(<FullyAutomaticGradingBadge />);
    expect(screen.getByText('Fully automatic grading')).toBeInTheDocument();
  });

  it('renders AutomaticGradingBadge with correct text', () => {
    render(<AutomaticGradingBadge />);
    expect(screen.getByText('Automatic grading')).toBeInTheDocument();
  });

  it('renders ManualGradingBadge with correct text', () => {
    render(<ManualGradingBadge />);
    expect(screen.getByText('Manual grading')).toBeInTheDocument();
  });

  it('renders CreatedAssignmentBadge with correct text', () => {
    render(<CreatedAssignmentBadge />);
    expect(screen.getByText('Not released')).toBeInTheDocument();
  });

  it('renders ReleasedAssignmentBadge with correct text', () => {
    render(<ReleasedAssignmentBadge />);
    expect(screen.getByText('Released')).toBeInTheDocument();
  });

  it('renders CompletedAssignmentBadge with correct text', () => {
    render(<CompletedAssignmentBadge />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });
});
