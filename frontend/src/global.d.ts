// TypeScript declaration for .jsx modules
// Allows importing .jsx files in TS/TSX without type errors
declare module '*.jsx' {
  import * as React from 'react';
  const component: React.ComponentType<any>;
  export default component;
}
