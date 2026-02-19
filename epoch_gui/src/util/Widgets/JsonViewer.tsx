import {Box, Dialog, DialogContent, DialogTitle, IconButton, Tooltip} from "@mui/material";
import * as React from "react";
import DataObjectIcon from '@mui/icons-material/DataObject';
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import {usePresentationMode} from "../../PresentationMode.tsx";


interface JsonViewerProps {
    data: any;
    name?: string;
}


const mono = { fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace" };


const JsonViewer: React.FC<JsonViewerProps> = ({data, name}) => {

    const [viewerOpen, setViewerOpen] = React.useState(false);


    const handleCopy = React.useCallback(() => {
        try {
            navigator.clipboard.writeText(JSON.stringify(data, null, 2));
        } catch {
            // no-op
        }
    }, [data]);

    const { enabled: isPresentationMode } = usePresentationMode();
    if (isPresentationMode) {
        // only show the JSON Viewer when we're not in Presentation Mode
        return null;
    }

    return (
        <>
            <IconButton size="small" onClick={() => setViewerOpen(true)} aria-label="View raw JSON">
                <DataObjectIcon fontSize="small"/>
            </IconButton>
            <Dialog open={viewerOpen} onClose={() => setViewerOpen(false)} fullWidth maxWidth="md">
                <DialogTitle sx={{display: 'flex', alignItems: 'center', gap: 1}}>
                    <Box component="span" sx={{flex: 1}}>
                        {name ?? 'Raw JSON'}
                    </Box>
                    <Tooltip title="Copy JSON">
                        <span>
                        <IconButton size="small" onClick={handleCopy} aria-label="Copy JSON">
                            <ContentCopyIcon fontSize="small"/>
                        </IconButton>
                        </span>
                    </Tooltip>
                </DialogTitle>

                <DialogContent dividers>
                    <Box component="pre" sx={{...mono, m: 0, fontSize: 13}}>
                        {JSON.stringify(data, null, 2)}
                    </Box>
                </DialogContent>
            </Dialog>
        </>
    )
}

export default JsonViewer;
