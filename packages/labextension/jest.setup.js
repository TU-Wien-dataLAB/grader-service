// jest.setup.js
import '@testing-library/jest-dom';

Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
    readText: jest.fn()
  }
});
