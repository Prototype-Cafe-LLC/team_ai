# E2E Tests for Multi-Agent Development System

This directory contains end-to-end tests using Playwright for the Multi-Agent Development System.

## Setup

1. Install dependencies:

```bash
npm install
```

2. Install Playwright browsers:

```bash
npm run playwright:install
```

## Running Tests

### Run all tests

```bash
npm test
```

### Run tests in headed mode (see browser)

```bash
npm run test:headed
```

### Debug tests

```bash
npm run test:debug
```

### Use Playwright UI mode

```bash
npm run test:ui
```

## Test Description

The main test file `create-hello-world.spec.ts` contains tests that:

1. **Create Hello World Project**: Tests the full workflow of creating a simple "Hello World" web page through the multi-agent system
   - Fills in project requirements
   - Monitors progress through all 4 phases (Requirements, Design, Implementation, Test)
   - Verifies that HTML and CSS code is generated
   - Checks that tests are created

2. **Pause and Resume**: Tests the ability to pause and resume a project during development

3. **Error Handling**: Tests that the system properly handles validation errors

## Test Structure

- `tests/` - Contains all test specifications
- `playwright.config.ts` - Playwright configuration
- `package.json` - Test dependencies and scripts

## Prerequisites

Before running tests, ensure:

1. The Multi-Agent Development System is running (backend and frontend)
2. You have set the `ANTHROPIC_API_KEY` in the parent `.env` file
3. Services are accessible at:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

The Playwright configuration automatically starts the Docker containers if they're not already running.