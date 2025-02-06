// theme.ts
import { createTheme, ThemeOptions } from '@mui/material/styles';


// These colours have been picked out of the Elemental Power Logo SVG

const lightThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: { main: '#76B5BF' },
    secondary: { main: '#B7BD55' },
    warning: { main: '#FED654' },
    error: { main: '#E16A56' },
    background: { default: '#f5f5f5', paper: '#ffffff' },
    text: { primary: '#333', secondary: '#555' },
  },
};

const darkThemeOptions: ThemeOptions = {
  palette: {
    mode: 'dark',
    primary: { main: '#76B5BF' },
    secondary: { main: '#B7BD55' },
    warning: { main: '#FED654' },
    error: { main: '#E16A56' },
    background: { default: '#121212', paper: '#1e1e1e' },
    text: { primary: '#fff', secondary: '#ddd' },
  },
};

export function getAppTheme(isDarkMode: boolean) {
  const themeOptions = isDarkMode ? darkThemeOptions : lightThemeOptions;
  return createTheme(themeOptions);
}
