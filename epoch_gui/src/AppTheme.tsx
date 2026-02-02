import * as React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import GlobalStyles from '@mui/material/GlobalStyles';
import { getAppTheme } from './Themes.ts';

type Props = {
  children: React.ReactNode;
  isDarkMode: boolean;
  isInformedEmbed?: boolean;
};

export default function AppTheme({ children, isDarkMode, isInformedEmbed = false }: Props) {
  const theme = React.useMemo(
    () => getAppTheme(isDarkMode, isInformedEmbed),
    [isDarkMode, isInformedEmbed]
  );

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyles
        styles={(t) => ({

        ':root': {
          fontFamily: t.typography.fontFamily,
          lineHeight: 1.5,
          fontWeight: 400,
          colorScheme: t.palette.mode,
          fontSynthesis: 'none',
          textRendering: 'optimizeLegibility',
          WebkitFontSmoothing: 'antialiased',
          MozOsxFontSmoothing: 'grayscale',
        },

        body: {
          margin: 0,
          minWidth: 320,
          minHeight: '100vh',
          backgroundColor: t.palette.background.default,
          color: t.palette.text.primary,
        },

        '#root': {
          margin: '0 auto',
          padding: '2rem',
          textAlign: 'center',
          backgroundColor: 'transparent',
        },

        h1: { fontSize: '3.2em', lineHeight: 1.1 },

        '.fixed-tabs': {
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          zIndex: 1000,
          borderBottom: '100px solid t.palette.divider',
          backgroundColor: t.palette.background.paper,
        },

        '.content': { marginTop: 48 },
        '.card': { padding: '2em' },
      })}
      />
      {children}
    </ThemeProvider>
  );
}
