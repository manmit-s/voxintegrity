module.exports = {
  env: { browser: true, es2021: true, node: true },
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: { jsx: true },
  },
  rules: {
    // JSX component imports are consumed by the JSX transform. This lightweight
    // config intentionally avoids adding another eslint plugin just to mark them.
    'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z]' }],
    'no-extra-semi': 'off',
  },
  ignorePatterns: ['dist/', 'node_modules/'],
}
