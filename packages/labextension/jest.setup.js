import '@testing-library/jest-dom';

jest.mock('yjs');

// Mock Navigator Clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
    readText: jest.fn()
  }
});

// Layout & Dimensions Mocks
Element.prototype.getBoundingClientRect = jest.fn(() => ({
  width: 120,
  height: 40,
  top: 0,
  left: 0,
  bottom: 40,
  right: 120,
  x: 0,
  y: 0,
  toJSON: () => {}
}));

Element.prototype.scrollIntoView = jest.fn();
Element.prototype.hasPointerCapture = jest.fn().mockReturnValue(false);
Element.prototype.setPointerCapture = jest.fn();
Element.prototype.releasePointerCapture = jest.fn();

// ResizeObserver Mock
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  value: ResizeObserverMock
});

// MatchMedia Mock
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
});

// Animation Frames
global.requestAnimationFrame = cb => setTimeout(cb, 16);
global.cancelAnimationFrame = id => clearTimeout(id);

// UI Mocks
jest.mock('@floating-ui/dom', () => {
  const actual = jest.requireActual('@floating-ui/dom');
  return {
    ...actual,
    autoUpdate: jest.fn(() => () => {})
  };
});

// PointerEvent Polyfill for jsdom
class MockPointerEvent extends Event {
  button;
  ctrlKey;
  pointerId;
  pointerType;
  clientX;
  clientY;

  constructor(type, props = {}) {
    super(type, props);
    this.button = props.button ?? 0;
    this.ctrlKey = props.ctrlKey ?? false;
    this.pointerId = props.pointerId ?? 1;
    this.pointerType = props.pointerType ?? 'mouse';
    this.clientX = props.clientX ?? 0;
    this.clientY = props.clientY ?? 0;
  }
}

window.PointerEvent = MockPointerEvent;
