import { createTheme, ThemeOptions } from '@mui/material/styles';

const epochTypography = {
  fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif'
}

// These colours have been picked out of the Elemental Power Logo SVG
const epochPalette = {
  primary: {main: '#76B5BF'},
  secondary: {main: '#B7BD55'},
  warning: {main: '#FED654'},
  error: {main: '#E16A56'},
}

const lightThemeOptions: ThemeOptions = {
  palette: {
    ...epochPalette,
    mode: 'light',
    background: { default: '#f5f5f5', paper: '#ffffff' },

    text: { primary: '#333', secondary: '#555' },
  },
  typography: epochTypography
};

const darkThemeOptions: ThemeOptions = {
  palette: {
    ...epochPalette,
    mode: 'dark',
    background: { default: '#242424', paper: '#1e1e1e' },
    text: { primary: '#fff', secondary: '#ddd' },
  },
  typography: epochTypography
};

const informedTypography = {
  fontFamily: [
    '"NB Grotesk"',        // Informed Font (?)
    'Inter',               // clean modern sans (commonly installed / Google Fonts)
    'Helvetica Neue',      // modern macOS Helvetica
    'Helvetica',           // older macOS fallback
    'Arial',               // Windows safe sans
    'ui-sans-serif',       // modern CSS generic family
    'system-ui',           // OS default UI font
    '-apple-system',       // San Francisco on macOS/iOS
    'BlinkMacSystemFont',  // Chrome on macOS
    '"Segoe UI"',          // Windows default UI font
    'Roboto',              // Android / ChromeOS default
    '"Noto Sans"',         // Linux default
    'sans-serif',          // last resort
  ].join(','),
}

const informedDarkThemeOptions: ThemeOptions = {
  palette: {
    mode: 'dark',
    primary: { main: '#dcfbd0' },
    secondary: { main: '#dcfbd0' },
    warning: { main: '#de6f66' },
    error: { main: '#de6f66' },
    background: { default: '#203131', paper: '#1a2626' },
    text: { primary: '#dfd', secondary: '#dfd' },
  },
  typography: informedTypography,
};

const informedLightThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: { main: '#203131' },
    secondary: { main: '#203131' },
    warning: { main: '#de6f66' },
    error: { main: '#de6f66' },
    background: { default: '#dcfbd0', paper: '#dcfbd0' },
    text: { primary: '#232', secondary: '#232' },
  },
  typography: informedTypography,
};

export function getAppTheme(isDarkMode: boolean, isInformedEmbed: boolean = false) {
  // The Informed theme overrides the dark and light modes;
  // currently the light and dark modes are just swapped colours
  if (isInformedEmbed) {
    const themeOptions = isDarkMode ? informedDarkThemeOptions : informedLightThemeOptions;
    return createTheme(themeOptions);    
  }
  const themeOptions = isDarkMode ? darkThemeOptions : lightThemeOptions;
  return createTheme(themeOptions);
}
