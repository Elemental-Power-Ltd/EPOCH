import * as React from "react";
import { Alert, Box, useMediaQuery, useTheme } from "@mui/material";
import { usePresentationMode } from "../PresentationMode";

type Props = {
  children: React.ReactNode;
  /** Treat sm and below as "phone" by default */
  phoneBreakpoint?: "xs" | "sm" | "md";
  /** Message shown when rotation is required */
  message?: React.ReactNode;
  /** Optional wrapper styles */
  sx?: any;
};

export const SmallScreenRotationGuard: React.FC<Props> = ({
  children,
  phoneBreakpoint = "sm",
  message = "Please rotate your phone to landscape.",
  sx,
}) => {
  const { enabled: presentationMode } = usePresentationMode();

  const theme = useTheme();
  const isPortrait = useMediaQuery("(orientation: portrait)");
  const isPhone = useMediaQuery(theme.breakpoints.down(phoneBreakpoint));

  const shouldGuard = presentationMode && isPhone && isPortrait;

  return (
    <Box sx={sx}>
      {shouldGuard && <Alert severity="info">{message}</Alert>}

      <Box sx={{ display: shouldGuard ? "none" : "block", mt: shouldGuard ? 0 : 2 }}>
        {children}
      </Box>
    </Box>
  );
};
