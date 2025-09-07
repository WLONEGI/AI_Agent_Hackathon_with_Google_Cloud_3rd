const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

// Integration test specific configuration
const integrationJestConfig = {
  displayName: 'Integration Tests',
  setupFilesAfterEnv: ['<rootDir>/tests/helpers/jest.integration.setup.js'],
  testEnvironment: 'node', // Use node environment for real API calls
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testMatch: [
    '<rootDir>/tests/integration/**/*.test.{js,jsx,ts,tsx}',
    '<rootDir>/tests/contracts/**/*.test.{js,jsx,ts,tsx}',
  ],
  testPathIgnorePatterns: [
    '<rootDir>/.next/',
    '<rootDir>/node_modules/',
    '<rootDir>/tests/e2e/',
    '<rootDir>/tests/unit/'
  ],
  moduleDirectories: ['node_modules', '<rootDir>/'],
  collectCoverageFrom: [
    'src/lib/api.ts',
    'src/lib/websocket.ts',
    'src/hooks/useWebSocket.ts',
    'src/stores/**/*.ts'
  ],
  coverageDirectory: '<rootDir>/test-artifacts/integration-coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  testTimeout: 30000, // 30 seconds for integration tests
  maxWorkers: 1, // Run integration tests serially to avoid conflicts
  verbose: true,
  detectOpenHandles: true,
  forceExit: true,
  // Global test configuration
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json'
    }
  },
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }]
  },
  // Integration test specific environment variables
  setupFiles: ['<rootDir>/tests/helpers/integration.env.js']
}

module.exports = createJestConfig(integrationJestConfig)