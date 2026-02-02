import * as React from "react";
import {
  Dialog,
  DialogContent,
  IconButton,
  Typography,
  Box,
  Stack,
  Chip,
  DialogTitle,
  useMediaQuery
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import { useTheme } from "@mui/material/styles";

/**
 * Tip type for the ExplainerDialog
 */
export type ExplainerTip = {
  /** Optional unique id for React keying */
  id?: string | number;
  title: string;
  text: string;
  media: {
    /** "image" also supports animated gifs */
    type: "image" | "gif" | "video";
    /** Source URL for the media */
    src: string;
    /** Accessible alt text for images */
    alt?: string;
    /** Optional poster image for videos */
    poster?: string;
    /** Optional object fit for images/video (e.g., 'contain' | 'cover') */
    objectFit?: React.CSSProperties["objectFit"];
  };
};

export type ExplainerDialogProps = {
  /** Controls visibility from parent */
  open: boolean;
  /** The list of tips to show */
  tips: ExplainerTip[];
  /** Close handler */
  onClose: () => void;
  /** Optional initial tip index when opened */
  startIndex?: number;
  /** Optional title for the dialog header */
  dialogTitle?: string;
  /** Callback when the active tip index changes */
  onIndexChange?: (index: number) => void;
  /** If true, loop from end to start and vice‑versa */
  loopNavigation?: boolean;
  /** Max width of the dialog */
  maxWidth?: "xs" | "sm" | "md" | "lg" | "xl";
};

/**
 * A generic explainer component (MUI + TypeScript).
 *
 * - Controlled `open` prop to show/hide the dialog from elsewhere in your app.
 * - Accepts a list of tips (image/gif/video + title + text).
 * - Side arrows (and keyboard arrows) to navigate forward/backward.
 * - Optional looping, progress chip, and responsive layout.
 */
export function ExplainerDialog({
  open,
  tips,
  onClose,
  startIndex = 0,
  dialogTitle = "How it works",
  onIndexChange,
  loopNavigation = false,
  maxWidth = "md",
}: ExplainerDialogProps) {
  const theme = useTheme();
  const isSmall = useMediaQuery(theme.breakpoints.down("sm"));

  const [index, setIndex] = React.useState(() => clampIndex(startIndex, tips.length));

  // Reset to startIndex whenever dialog opens or startIndex changes
  React.useEffect(() => {
    if (open) {
      setIndex(clampIndex(startIndex, tips.length));
    }
  }, [open, startIndex, tips.length]);

  // Notify parent of index change
  React.useEffect(() => {
    onIndexChange?.(index);
  }, [index, onIndexChange]);

  // Keyboard navigation when dialog is open
  React.useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goPrev();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goNext();
      } else if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, index, tips.length, loopNavigation]);

  const atStart = index === 0;
  const atEnd = index === tips.length - 1;

  const goPrev = () => {
    if (tips.length === 0) return;
    if (atStart) {
      if (loopNavigation) setIndex(tips.length - 1);
    } else {
      setIndex((i) => i - 1);
    }
  };

  const goNext = () => {
    if (tips.length === 0) return;
    if (atEnd) {
      if (loopNavigation) setIndex(0);
    } else {
      setIndex((i) => i + 1);
    }
  };

  const activeTip = tips[index];

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth={maxWidth}
      fullWidth
      aria-labelledby="explainer-dialog-title"
    >
      <DialogTitle id="explainer-dialog-title" sx={{ pr: 8 }}>
        {dialogTitle}
        <IconButton
          aria-label="Close"
          onClick={onClose}
          sx={{ position: "absolute", right: 12, top: 12 }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ position: "relative", pt: 0 }}>
        {/* Progress chip */}
        {tips.length > 0 && (
          <Box sx={{ position: "absolute", top: 12, left: 16, zIndex: 2 }}>
            <Chip label={`${index + 1} / ${tips.length}`} size={isSmall ? "small" : "medium"} />
          </Box>
        )}

        {/* Left Arrow */}
        <IconButton
          aria-label="Previous"
          onClick={goPrev}
          disabled={!loopNavigation && atStart}
          sx={{
            position: "absolute",
            top: "50%",
            left: 8,
            transform: "translateY(-50%)",
            zIndex: 2,
            bgcolor: "background.paper",
            boxShadow: 1,
            "&:hover": { bgcolor: "background.paper" },
          }}
          size={isSmall ? "small" : "medium"}
        >
          <ArrowBackIosNewIcon />
        </IconButton>

        {/* Right Arrow */}
        <IconButton
          aria-label="Next"
          onClick={goNext}
          disabled={!loopNavigation && atEnd}
          sx={{
            position: "absolute",
            top: "50%",
            right: 8,
            transform: "translateY(-50%)",
            zIndex: 2,
            bgcolor: "background.paper",
            boxShadow: 1,
            "&:hover": { bgcolor: "background.paper" },
          }}
          size={isSmall ? "small" : "medium"}
        >
          <ArrowForwardIosIcon />
        </IconButton>

        {/* Main content */}
        {activeTip ? (
          <Stack spacing={2} alignItems="center">
            <MediaView key={activeTip.id ?? index} tip={activeTip} />
            <Box sx={{ width: "100%" }}>
              <Typography variant="h6" gutterBottom>
                {activeTip.title}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {activeTip.text}
              </Typography>
            </Box>
          </Stack>
        ) : (
          <Box sx={{ p: 3 }}>
            <Typography variant="body1" color="text.secondary">
              No tips to display.
            </Typography>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
}

function clampIndex(idx: number, len: number) {
  if (len <= 0) return 0;
  return Math.max(0, Math.min(len - 1, idx));
}

/** Renders the media area for a tip (image/gif/video) */
function MediaView({ tip }: { tip: ExplainerTip }) {
  const theme = useTheme();
  const isSmall = useMediaQuery(theme.breakpoints.down("sm"));

  const maxH = isSmall ? 360 : 660;

  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  // Ensure any playing video is stopped when this MediaView unmounts
  React.useEffect(() => {
    return () => {
      const v = videoRef.current;
      if (v) {
        try { v.pause(); } catch {}
        // Unset src and force a load to fully stop network/decoder in some browsers
        v.removeAttribute("src");
        try { v.load(); } catch {}
      }
    };
  }, []);

  if (tip.media.type === "video") {
    return (
      <Box sx={{ width: "100%", display: "flex", justifyContent: "center" }}>
        <Box
          component="video"
          ref={videoRef}
          controls
          autoPlay
          muted
          loop
          poster={tip.media.poster}
          preload="metadata"
          sx={{
            width: "100%",
            maxHeight: maxH,
            borderRadius: 2,
            boxShadow: 1,
            objectFit: tip.media.objectFit ?? "contain",
          }}
        >
          <source src={tip.media.src} />
          {/* Fallback text for browsers without video support */}
          Your browser does not support the video tag.
        </Box>
      </Box>
    );
  }

  // Treat GIFs as images so they can autoplay
  return (
    <Box sx={{ width: "100%", display: "flex", justifyContent: "center" }}>
      <Box
        component="img"
        src={tip.media.src}
        alt={tip.media.alt ?? tip.title}
        loading="lazy"
        sx={{
          width: "100%",
          maxHeight: maxH,
          borderRadius: 2,
          boxShadow: 1,
          objectFit: tip.media.objectFit ?? "contain",
        }}
      />
    </Box>
  );
}
