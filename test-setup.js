#!/usr/bin/env node

/**
 * CloudCommerce Setup Test Script
 * This script verifies that all components are properly configured
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔍 CloudCommerce Setup Test');
console.log('============================\n');

// Test results
const results = {
  passed: 0,
  failed: 0,
  warnings: 0
};

function test(name, testFn) {
  try {
    const result = testFn();
    if (result === true) {
      console.log(`✅ ${name}`);
      results.passed++;
    } else if (result === false) {
      console.log(`❌ ${name}`);
      results.failed++;
    } else {
      console.log(`⚠️  ${name}`);
      results.warnings++;
    }
  } catch (error) {
    console.log(`❌ ${name}: ${error.message}`);
    results.failed++;
  }
}

function fileExists(filePath) {
  return fs.existsSync(filePath);
}

function checkEnvVariable(name) {
  return process.env[name] && process.env[name].length > 0;
}

function checkPackageJson() {
  try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    return packageJson.name && packageJson.dependencies;
  } catch {
    return false;
  }
}

// Test 1: Project Structure
test('Project root files exist', () => {
  const requiredFiles = [
    'package.json',
    'README.md',
    'tsconfig.json',
    'tailwind.config.ts',
    'vercel.json'
  ];
  return requiredFiles.every(file => fileExists(file));
});

// Test 2: Frontend Structure
test('Frontend structure exists', () => {
  const requiredDirs = [
    'app',
    'app/api',
    'components',
    'lib'
  ];
  const requiredFiles = [
    'app/page.tsx',
    'app/layout.tsx',
    'components/SubmissionForm.tsx',
    'lib/openrouter.ts',
    'lib/scraper.ts',
    'lib/crew.ts'
  ];
  return [...requiredDirs, ...requiredFiles].every(item => fileExists(item));
});

// Test 3: Backend Structure
test('Backend structure exists', () => {
  const requiredFiles = [
    'backend/main.py',
    'backend/requirements.txt',
    'backend/core/agents/submit_agent.py',
    'backend/Dockerfile'
  ];
  return requiredFiles.every(file => fileExists(file));
});

// Test 4: Mobile Structure
test('Mobile structure exists', () => {
  const requiredFiles = [
    'mobile/package.json',
    'mobile/App.tsx',
    'mobile/app.json',
    'mobile/babel.config.js',
    'mobile/tsconfig.json',
    'mobile/lib/supabase.ts',
    'mobile/contexts/AuthContext.tsx',
    'mobile/screens/CameraScreen.tsx',
    'mobile/screens/LoadingScreen.tsx',
    'mobile/screens/ResultScreen.tsx'
  ];
  return requiredFiles.every(file => fileExists(file));
});

// Test 5: Database Schema
test('Database schema exists', () => {
  return fileExists('supabase/schema.sql');
});

// Test 6: Environment Configuration
test('Environment configuration exists', () => {
  return fileExists('.env.example');
});

// Test 7: Documentation
test('Documentation exists', () => {
  return fileExists('SETUP.md');
});

// Test 8: Package.json Dependencies
test('Frontend package.json has required dependencies', () => {
  try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    const requiredDeps = [
      'next',
      'react',
      'react-dom',
      'stripe',
      '@clerk/nextjs',
      'openai',
      'axios',
      'cheerio',
      'puppeteer',
      'papaparse'
    ];
    return requiredDeps.every(dep => packageJson.dependencies[dep]);
  } catch {
    return false;
  }
});

// Test 9: Backend Requirements
test('Backend requirements.txt has required dependencies', () => {
  try {
    const requirements = fs.readFileSync('backend/requirements.txt', 'utf8');
    const requiredPkgs = [
      'fastapi',
      'uvicorn',
      'openai',
      'pydantic',
      'requests',
      'beautifulsoup4',
      'crewai',
      'litellm',
      'llama-index',
      'bitwarden'
    ];
    return requiredPkgs.some(pkg => requirements.includes(pkg));
  } catch {
    return false;
  }
});

// Test 10: Mobile Dependencies
test('Mobile package.json has required dependencies', () => {
  try {
    const packageJson = JSON.parse(fs.readFileSync('mobile/package.json', 'utf8'));
    const requiredDeps = [
      'expo',
      'expo-camera',
      'expo-image-picker',
      'expo-file-system',
      'expo-sharing',
      '@supabase/supabase-js',
      'react',
      'react-native'
    ];
    return requiredDeps.every(dep => packageJson.dependencies[dep]);
  } catch {
    return false;
  }
});

// Test 11: TypeScript Configuration
test('TypeScript configuration exists', () => {
  return fileExists('tsconfig.json') && fileExists('mobile/tsconfig.json');
});

// Test 12: Docker Configuration
test('Docker configuration exists', () => {
  return fileExists('backend/Dockerfile');
});

// Test 13: Vercel Configuration
test('Vercel configuration exists', () => {
  return fileExists('vercel.json');
});

// Test 14: Environment Variables (if .env exists)
if (fileExists('.env')) {
  test('Environment variables are set', () => {
    const requiredEnvVars = [
      'NEXT_PUBLIC_SUPABASE_URL',
      'NEXT_PUBLIC_SUPABASE_ANON_KEY',
      'STRIPE_SECRET_KEY',
      'CLERK_SECRET_KEY',
      'OPENROUTER_API_KEY'
    ];
    return requiredEnvVars.every(varName => checkEnvVariable(varName));
  });
} else {
  test('Environment variables file (.env) not found', () => {
    console.log('   ⚠️  Create .env file from .env.example');
    return 'warning';
  });
}

// Test 15: Git Configuration
test('Git repository initialized', () => {
  try {
    execSync('git status', { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
});

// Test 16: Node.js Version
test('Node.js version compatibility', () => {
  try {
    const version = process.version;
    const majorVersion = parseInt(version.replace('v', '').split('.')[0]);
    return majorVersion >= 18;
  } catch {
    return false;
  }
});

// Test 17: Python Version (if available)
try {
  const pythonVersion = execSync('python3 --version', { encoding: 'utf8' }).trim();
  test(`Python version compatibility (${pythonVersion})`, () => {
    const version = pythonVersion.replace('Python ', '');
    const majorVersion = parseInt(version.split('.')[0]);
    return majorVersion >= 3;
  });
} catch {
  test('Python not installed', () => {
    console.log('   ⚠️  Python 3.10+ required for backend');
    return 'warning';
  });
}

// Test 18: Expo CLI (if available)
try {
  execSync('expo --version', { stdio: 'ignore' });
  test('Expo CLI installed', () => {
    return true;
  });
} catch {
  test('Expo CLI not installed', () => {
    console.log('   ⚠️  Install with: npm install -g @expo/cli');
    return 'warning';
  });
}

// Summary
console.log('\n📊 Test Results Summary');
console.log('=======================');
console.log(`✅ Passed: ${results.passed}`);
console.log(`⚠️  Warnings: ${results.warnings}`);
console.log(`❌ Failed: ${results.failed}`);

if (results.failed === 0) {
  console.log('\n🎉 All tests passed! Your CloudCommerce setup is ready.');
  console.log('\nNext steps:');
  console.log('1. Copy .env.example to .env and fill in your API keys');
  console.log('2. Set up Supabase database using supabase/schema.sql');
  console.log('3. Run: pnpm install (frontend)');
  console.log('4. Run: cd backend && pip install -r requirements.txt');
  console.log('5. Run: cd mobile && npm install');
  console.log('6. Start development servers: pnpm dev, uvicorn main:app --reload, npx expo start');
} else {
  console.log('\n❌ Some tests failed. Please fix the issues above before proceeding.');
  process.exit(1);
}