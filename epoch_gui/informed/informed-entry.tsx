import React from 'react';
import ReactDOM from 'react-dom/client';

import AppTheme from "../src/AppTheme";

import {DataVizFileWrapper} from "./dataviz-wrapper";
import {SiteDataFileWrapper} from "./sitedata-wrapper";
import {Alert, Box} from "@mui/material";


type View = 'dataviz' | 'sitedata' | 'error';

const parseHashView = (hash: string): View => {
    // we use hash routing as a workaround to keep the hosting simple for Holosphere
    // (this is the only way to ship a single file and do some form of routing)

    // we accept "#/dataviz" or "#dataviz" (and same for sitedata)
    const h = hash.replace(/^#/, '');
    const seg = h.startsWith('/') ? h.slice(1) : h;
    if (seg.toLowerCase().startsWith('sitedata')) return 'sitedata';
    return 'dataviz';
};

function InformedEntry() {
    // get the theme from query params
    const params = new URLSearchParams(window.location.search);
    const mode = params.get('mode') ?? '0';
    // 0 - isInformedEmbed, isDarkMode
    // 1 - isInformedEmbed, !isDarkMode
    // 2 - !isInformedEmbed, isDarkMode
    // 3 - !isInformedEmbed, !isDarkMode
    const isDarkMode = mode === '0' || mode === '2';
    const isInformedTheme = mode === '0' || mode === '1';

    const hasData = params.has('data');
    const hasSite = params.has('site');

    let view = 'error'
    if (hasData && !hasSite) {
        view = 'dataviz';
    } else if (!hasData && hasSite) {
        view = 'sitedata';
    }

    return (
        <AppTheme isDarkMode={isDarkMode} isInformedEmbed={isInformedTheme}>
            {view === 'dataviz' && <DataVizFileWrapper/>}
            {view === 'sitedata' && <SiteDataFileWrapper/>}
            {view === 'error' && (
                <Box m={2}>
                    <Alert severity="error">Must provide either a site param or a data param</Alert>
                </Box>)}
        </AppTheme>
    )
}


ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <InformedEntry/>
    </React.StrictMode>
);
